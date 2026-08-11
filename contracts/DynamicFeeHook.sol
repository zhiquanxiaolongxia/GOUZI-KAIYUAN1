// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

/**
 * DynamicFeeHook —— 逆向自 Robinhood 链 (chainId 4663) 上的 5131 字节 hook
 *   三代 0x31Ac5B793C073C7EB15CfC259963CD60004f4080 (USDG/FRONG)
 *   五代 0x42554Fa546995A393D19B3880D3a4C6709298080 (ETH/xxx)
 *   两者 codehash 完全相同，仅配置不同。
 *
 * 核心机制（已由 anvil fork + debug_traceCall 逐 opcode 实证）：
 *   beforeSwap 里读 gasleft()，与 gasThreshold(=5,000,000) 比较。
 *   gasleft() >= 阈值  -> 免费 (lpFee = 0)
 *   gasleft() <  阈值  -> 按档收费
 *
 * 为什么这招有效：
 *   套利机器人为省 gas 精确设置 gasLimit（实测 23万~135万），
 *   普通前端路由给足余量（实测 600万~1000万，常见 7,500,004 / 10,000,000）。
 *   于是 gasleft() 成了"来者是不是套利者"的天然指纹——
 *   不需要白名单、不需要读价格、不需要任何外部调用。
 *
 * 实证数据（三代池 325 笔 swap）：
 *   收费 19 笔 -> gasLimit 全部 < 5,000,000（100%，零漏报）
 *   免费笔中位 gasLimit = 7,500,004
 *   临界点实测 5,024,658 = 5,000,000 + 24,658（hook 入口前开销）
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
    using LPFeeLibrary for uint24;

    error NotOwner();
    error FeeTooLarge();

    event FeeConfigUpdated(
        uint24 tier1, uint24 tier2, uint24 tier3,
        uint24 thr1, uint24 thr2, uint24 thr3,
        uint256 gasThreshold
    );

    // ---- slot0 ----
    address public owner;

    // ---- slot1: 三档费率，链上实测按 uint24 紧密打包 ----
    // 三代: 48000 / 95000 / 150000   (4.8% / 9.5% / 15%)
    // 五代: 48000 / 75000 / 100000   (4.8% / 7.5% / 10%)
    uint24 public tier1Fee;
    uint24 public tier2Fee;
    uint24 public tier3Fee;

    // ---- slot2: 三档阈值 ----
    // 三代: 7500 / 1000 / 1000      五代: 6000 / 2000 / 1000
    uint24 public tier1Threshold;
    uint24 public tier2Threshold;
    uint24 public tier3Threshold;

    // ---- slot3: gas 门槛，两代均为 5,000,000（硬编码同值）----
    uint256 public gasThreshold;

    // ---- slot4: mapping(poolId => swap 计数器)，每笔 +1，不参与定价 ----
    mapping(PoolId => uint256) public swapCount;

    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner();
        _;
    }

    constructor(
        IPoolManager _manager,
        uint24 _tier1, uint24 _tier2, uint24 _tier3,
        uint24 _thr1,  uint24 _thr2,  uint24 _thr3,
        uint256 _gasThreshold
    ) BaseHook(_manager) {
        owner = msg.sender;
        tier1Fee = _tier1; tier2Fee = _tier2; tier3Fee = _tier3;
        tier1Threshold = _thr1; tier2Threshold = _thr2; tier3Threshold = _thr3;
        gasThreshold = _gasThreshold;
    }

    /// 权限位 0x0080 —— 只开 beforeSwap，与链上实测一致
    function getHookPermissions() public pure override returns (Hooks.Permissions memory) {
        return Hooks.Permissions({
            beforeInitialize: false, afterInitialize: false,
            beforeAddLiquidity: false, afterAddLiquidity: false,
            beforeRemoveLiquidity: false, afterRemoveLiquidity: false,
            beforeSwap: true,   // <-- 唯一开启
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
        // 计数器 +1（原版有此行为，纯统计，不进定价）
        unchecked { swapCount[key.toId()] += 1; }

        uint24 fee = 0;
        if (gasleft() < gasThreshold) {
            fee = tier1Fee;   // 原版实测：命中即 tier1，多档预留给更细的策略
        }

        // bit22 = OVERRIDE_FLAG，告诉 PoolManager 用这个 lpFee 覆盖池子默认费率
        return (
            BaseHook.beforeSwap.selector,
            BeforeSwapDeltaLibrary.ZERO_DELTA,
            fee | LPFeeLibrary.OVERRIDE_FEE_FLAG
        );
    }

    function setFeeConfig(
        uint24 _tier1, uint24 _tier2, uint24 _tier3,
        uint24 _thr1,  uint24 _thr2,  uint24 _thr3,
        uint256 _gasThreshold
    ) external onlyOwner {
        if (_tier1 > 1_000_000 || _tier2 > 1_000_000 || _tier3 > 1_000_000) revert FeeTooLarge();
        tier1Fee = _tier1; tier2Fee = _tier2; tier3Fee = _tier3;
        tier1Threshold = _thr1; tier2Threshold = _thr2; tier3Threshold = _thr3;
        gasThreshold = _gasThreshold;
        emit FeeConfigUpdated(_tier1,_tier2,_tier3,_thr1,_thr2,_thr3,_gasThreshold);
    }

    function transferOwnership(address n) external onlyOwner { owner = n; }

    function getFeeConfig() external view returns (
        uint24,uint24,uint24,uint24,uint24,uint24,uint256
    ) {
        return (tier1Fee,tier2Fee,tier3Fee,tier1Threshold,tier2Threshold,tier3Threshold,gasThreshold);
    }
}
