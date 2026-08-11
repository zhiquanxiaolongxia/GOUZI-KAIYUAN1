# HOOK-KAIYUAN1

Uniswap V4 动态费率 Hook 逆向工程报告 —— Robinhood 链 (chainId 4663)

---

## 一句话结论

这个 hook 的判罚机制就是一行代码：

```solidity
if (gasleft() < 5_000_000) fee = 48000;  // 4.8%
else                       fee = 0;      // 免费
```

**它通过 `gasleft()` 识别套利机器人**：套利者为省成本精确掐 gasLimit（实测 23万~135万），普通前端路由给足余量（7,500,004 / 10,000,000 这类默认值）。于是剩余 gas 成了"来者是不是套利者"的天然指纹 —— 不需要白名单、不需要读价格、不需要任何外部调用。

---

## 目标合约

| 代次 | 地址 | 池 | owner |
|---|---|---|---|
| 三代 | `0x31Ac5B793C073C7EB15CfC259963CD60004f4080` | USDG/FRONG | `0xc604AE8E12Bc9B55E1729BeD1A985Bb9a1224709` |
| 五代 | `0x42554Fa546995A393D19B3880D3a4C6709298080` | ETH/xxx | `0x789150Ad7e5F3b56a6ce5c71e531a30cCdfAD226` |

两者 **codehash 完全相同**（`4712c3c6…215f`，5131 字节），仅配置参数不同。

---

## 证据链

### 1. opcode 级抓现行

anvil fork + `debug_traceCall` 逐指令 dump，`beforeSwap` 内部只有 3 次 storage 访问和 1 个决定性比较：

```
step 215  GAS      → 0x3ffffffff9fae        ← 判据来源就是 GAS 指令
step 467  SLOAD    keccak(poolId,4) → 4     ← swap 计数器
step 473  SSTORE   keccak(poolId,4) ← 5     ← 计数器 +1
step 490  SLOAD    slot3 → 0x4c4b40 (5,000,000)
step 491  LT       5000000 < gasleft()
step 497  JUMPI    true → 免费 / false → 收费
```

### 2. 受控实验：只改 gas limit

金额、sender、方向全部锁死，唯一变量是 `eth_call` 的 gas：

| gas limit | fee |
|---|---|
| 100,000 → 5,000,000 | **48000（收费）** |
| **5,024,658** | **48000（临界最后一格）** |
| **5,024,659** | **0（免费）** |
| 5,100,000 → 30,000,000 | 0（免费） |

临界点 `5,024,658 − 24,658 = 5,000,000`，**精确等于 slot3**。
差值 24,658 是 hook 入口前的 gas 开销。

### 3. 真实链上数据反验（三代池 140 笔 tx）

| | gasLimit < 5M | gasLimit ≥ 5M |
|---|---|---|
| **实际收费 19 笔** | **19（100%）** | **0（零漏报）** |
| 实际免费 121 笔 | 11 | 110 |

- 收费笔 gasLimit 中位数：**673,289**
- 免费笔 gasLimit 中位数：**7,500,004**

那 11 个"误报"不是模型错 —— hook 判的是 `gasleft()`，比 tx 的 gasLimit 少了路由消耗，完全自洽。

---

## Storage 布局

```
slot0  address owner
slot1  [tier3][tier2][tier1][dynFlag]   三个 uint24 费率 + 0x800000
slot2  [thr1][thr2][thr3]               三个 uint24 阈值
slot3  uint256 gasThreshold             = 5,000,000（两代相同，硬编码常量）
slot4  mapping(poolId => uint256)       swap 计数器，每笔 +1，不参与定价
```

### 配置对照

| | 三代 USDG/FRONG | 五代 ETH/xxx |
|---|---|---|
| tier1 | 48000 (4.8%) | 48000 (4.8%) |
| tier2 | 95000 (9.5%) | 75000 (7.5%) |
| tier3 | 150000 (15%) | 100000 (10%) |
| gasThreshold | 5,000,000 | 5,000,000 |

---

## 安全审计结论

字节码逐 opcode 扫描（5131 字节）：

| opcode | 次数 | 含义 |
|---|---|---|
| `CALL` / `STATICCALL` / `DELEGATECALL` | **0** | 无任何外部调用 |
| `CREATE` / `CREATE2` / `SELFDESTRUCT` | **0** | 无部署、无自毁 |
| `TLOAD` / `TSTORE` | **0** | 不用 transient storage |
| `SLOAD` / `SSTORE` | 44 / 10 | 仅读写自身配置与计数器 |

**owner 物理上拿不走一分钱** —— 没有 `take`/`donate`/`transfer` 选择器，唯一硬编码地址是 PoolManager `0x8366a39CC670B4001A1121B8F6A443A643e40951`。

推论：这个 hook **物理上看不见池价**（无外部调用），所以一切"价格偏离判罚"的叙事都不成立。

---

## 已知局限（诚实声明）

1. **多档费率（tier2/tier3）的触发条件未解出**。真实链上确有 95000 / 150000 档出现，但分界线未找到。本仓库的 Solidity 实现是**降级版：命中即 tier1**。
2. **阈值 `7500/1000/1000`（五代 `6000/2000/1000`）物理含义未定**，slot2 字节切分存疑。
3. **本结论仅适用于 5131 字节 / 权限位 0x0080 的克隆系**。`0xc4` 升级版（8946 字节，带 afterSwap）是另一套字节码，不可混用。

---

## 机制弱点（重要）

**这个机制可以被绕过。** 套利者只要把 gasLimit 提到 500 万以上就免费了，代价仅仅是多付一点 gas —— 在 Orbit 链上几乎为零。

它现在有效，纯粹是因为对手还不知道判据是 `gasleft()`。**不建议直接照抄用于生产。**

---

## 目录结构

```
├── contracts/DynamicFeeHook.sol   可编译实现（已与原版字节码逐点比对）
├── analysis/                      机制推导与配置对照
├── scripts/                       全部验证脚本（可复现）
└── data/                          链上数据快照
```

## 复现方法

```bash
# 起 fork 节点（绕开远端 RPC 的 debug_* 封禁）
anvil --fork-url https://robinhood.rpc.blxrbdn.com \
      --fork-block-number 33147572 --port 8546

# 决定性实验：gas 临界点二分
python scripts/gasproof.py

# 真实 tx 反验
python scripts/realproof.py
```

---

## 逆向过程中踩的坑

| 坑 | 后果 |
|---|---|
| **poolKey 的 currency0/1 填错** | 查了一个不存在的池，hook 走 default 分支恒返回 0，白跑两轮 |
| **返回值偏移读错**（读 36，实际在 **64**） | 所有 fee 扫描全是假阴性，一度用 bug 亲手否掉了正确答案 |

`beforeSwap` 返回 96 字节，**费率在 word2（偏移 64）**：低 22 位是 lpFee，bit22 是 `OVERRIDE_FLAG`。
