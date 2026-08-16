// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

/**
 * DynamicFeeHook v2 —— 完全逆向自 Robinhood 链 (chainId 4663) 的 5131 字节 hook
 *   三代 0x31Ac5B793C073C7EB15CfC259963CD60004f4080 (USDG/FRONG)
 *   五代 0x42554Fa546995A393D19B3880D3a4C6709298080
 *
 * ============ 完整机制（两道关卡）============
 *
 * 关卡一：gas 门（身份过滤）
 *     if (gasleft() >= gasThreshold)  return 0;   // 免费放行
 *   套利机器人精确掐 gasLimit 省成本 → gasleft 低 → 进入关卡二
 *   普通前端路由给足余量(7.5M/10M) → 直接免费
 *
 * 关卡二：掷骰子（概率抽罚）
 *     r = keccak256(blockhash, prevrandao, timestamp, number, nonce...) % 10000
 *     r <  7500        -> tier1 (4.8%)   75%
 *     7500 <= r < 8500 -> tier2 (9.5%)   10%
 *     8500 <= r < 9500 -> tier3 (15%)    10%
 *     r >= 9500        -> 0  免费         5%
 *
 * ============ 实证依据 ============
 *  · opcode trace 抓到 MOD(keccak, 10000) -> r，及 AND 取出的 7500/1000/1000
 *  · 60 次受控采样：r 与 fee 边界零重叠，完美对齐 7500/8500/9500
 *  · 链上 51 笔收费实测 84.3%/9.8%/5.9%，卡方 1.256 < 5.99(df=2) 不拒绝
 *  · 同一 sender 0xa687b664 同时出现三档 → 证伪身份白名单模型
 *
 * ============ 安全审计 ============
 *  原版 opcode：CALL/DELEGATECALL/STATICCALL/CREATE/SELFDESTRUCT 全部为 0
 *  → hook 无转账能力，罚金 100% 归 LP，owner 拿不走一分钱
 *  本实现保持同等性质：无任何外部调用、无资金出口
 *
 * ============ 已知弱点（必读）============
 *  1. gas 门可绕过：套利者把 gasLimit 提到 >= 5M 即永久免费，成本几乎为零
 *  2. 伪随机可预测：blockhash/prevrandao/timestamp 在同块内对 MEV 搜索者已知，
 *     可模拟出 r 后择时提交，只在 r>=9500 时下单
 *  3. 二者叠加 → 本机制仅在"对手不知道判据"时有效，不适合作为长期招商产品
 */

import {BaseHook} from "v4-periphery/src/utils/BaseHook.sol";
import {Hooks} from "v4-core/src/libraries/Hooks.sol";
import {IPoolManager} from "v4-core/src/interfaces/IPoolManager.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";
import {BeforeSwapDelta, BeforeSwapDeltaLibrary} from "v4-core/src/types/BeforeSwapDelta.sol";
import {LPFeeLibrary} from "v4-core/src/libraries/LPFeeLibrary.sol";

contract DynamicFeeHook is BaseHook {
    using PoolIdLibrary for PoolKey;

    address public owner;

    // ---- 费率档（uint24, 百万分之一）----
    uint24 public tier1 = 48_000;    // 4.8%
    uint24 public tier2 = 95_000;    // 9.5%
    uint24 public tier3 = 150_000;   // 15%

    // ---- 概率阈值（万分之一）----
    // 三代 7500/1000/1000 ；五代 6000/2000/1000
    uint16 public thrA = 7500;   // r < thrA               -> tier1
    uint16 public thrB = 1000;   // thrA <= r < thrA+thrB   -> tier2
    uint16 public thrC = 1000;   // +thrC 区间             -> tier3
                                 // 其余（尾部）           -> 免费

    // ---- gas 门槛 ----
    uint256 public gasThreshold = 5_000_000;

    // ---- 每池 swap 计数器（充当随机数 nonce，slot4 实测用途）----
    mapping(PoolId => uint256) public swapCount;

    error NotOwner();
    event ConfigUpdated(uint24 t1, uint24 t2, uint24 t3, uint16 a, uint16 b, uint16 c, uint256 g);

    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner();
        _;
    }

    constructor(IPoolManager _pm) BaseHook(_pm) {
        owner = msg.sender;
    }

    function getHookPermissions() public pure override returns (Hooks.Permissions memory) {
        return Hooks.Permissions({
            beforeInitialize: false, afterInitialize: false,
            beforeAddLiquidity: false, afterAddLiquidity: false,
            beforeRemoveLiquidity: false, afterRemoveLiquidity: false,
            beforeSwap: true,                 // 权限位 0x0080 —— 地址必须用 CREATE2 挖出
            afterSwap: false,
            beforeDonate: false, afterDonate: false,
            beforeSwapReturnDelta: false, afterSwapReturnDelta: false,
            afterAddLiquidityReturnDelta: false, afterRemoveLiquidityReturnDelta: false
        });
    }

    function _beforeSwap(
        address,
        PoolKey calldata key,
        IPoolManager.SwapParams calldata,
        bytes calldata
    ) internal override returns (bytes4, BeforeSwapDelta, uint24) {
        PoolId id = key.toId();
        uint256 n = ++swapCount[id];          // 计数器自增（原版 slot4 行为）

        // ===== 关卡一：gas 门 =====
        if (gasleft() >= gasThreshold) {
            return (BaseHook.beforeSwap.selector,
                    BeforeSwapDeltaLibrary.ZERO_DELTA,
                    LPFeeLibrary.OVERRIDE_FEE_FLAG);      // fee = 0
        }

        // ===== 关卡二：掷骰子 =====
        uint256 r = uint256(keccak256(abi.encodePacked(
            blockhash(block.number - 1),
            block.prevrandao,
            block.timestamp,
            block.number,
            id,
            n
        ))) % 10_000;

        uint24 fee;
        if (r < thrA)                     fee = tier1;
        else if (r < uint256(thrA) + thrB) fee = tier2;
        else if (r < uint256(thrA) + thrB + thrC) fee = tier3;
        else                              fee = 0;        // 尾部免费

        return (BaseHook.beforeSwap.selector,
                BeforeSwapDeltaLibrary.ZERO_DELTA,
                fee | LPFeeLibrary.OVERRIDE_FEE_FLAG);
    }

    // ---------------- owner 调参 ----------------
    function setConfig(
        uint24 _t1, uint24 _t2, uint24 _t3,
        uint16 _a, uint16 _b, uint16 _c,
        uint256 _gas
    ) external onlyOwner {
        require(uint256(_a) + _b + _c <= 10_000, "prob>100%");
        require(_t1 <= 1_000_000 && _t2 <= 1_000_000 && _t3 <= 1_000_000, "fee too high");
        tier1 = _t1; tier2 = _t2; tier3 = _t3;
        thrA = _a; thrB = _b; thrC = _c;
        gasThreshold = _gas;
        emit ConfigUpdated(_t1, _t2, _t3, _a, _b, _c, _gas);
    }

    function transferOwnership(address to) external onlyOwner {
        owner = to;
    }
}
