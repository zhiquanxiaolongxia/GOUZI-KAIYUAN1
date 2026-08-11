# 脚本索引

按逆向流程的时间顺序排列。带 ⭐ 的是产出决定性结论的脚本。

## 环境依赖

```bash
# Python 环境（web3 / eth-abi）
~/.v4hook/bin/python

# anvil fork 节点（绕开远端 RPC 的 debug_* 403 封禁）
anvil --fork-url https://robinhood.rpc.blxrbdn.com \
      --fork-block-number 33147572 --port 8546
```

远端 RPC `https://robinhood.rpc.blxrbdn.com` 封禁了 `debug_traceCall` / `debug_traceTransaction` / `trace_transaction`（返回 403）。
`cast run` 也走不通 —— Arbitrum Orbit 的特殊 tx type 会导致 `deserialization error`。
**anvil fork 是唯一可行的 trace 路径。**

---

## 数据采集

| 脚本 | 作用 |
|---|---|
| `g3an.py` | 解析三代池 325 笔 swap，产出 `g3s.pkl`。费率档 4.8%/9.5%/15%，84.3% 免费 |
| `cfg.py` | 读取三代/五代 storage slot0-4 并拆解字段，两代配置对照 |

## 参数扫描（全部返回 fee=0 的阶段）

| 脚本 | 作用 |
|---|---|
| `fixkey.py` | **修正 poolKey** —— 发现此前 currency0/1 填错，构造了不存在的池 |
| `knobs.py` | 扫 sqrtPriceLimitX96 / hookData / gas 三个旋钮（此时返回值偏移仍是错的，结果为假阴性） |
| `probe3.py` | gas 差探针 |
| `tickan.py` | tick 漂移 vs 阈值假设（证伪） |

## 转折点

| 脚本 | 作用 |
|---|---|
| ⭐ `fix2.py` | **修正返回值解析** —— fee 在 word2（偏移 64）不是偏移 36。此前所有扫描作废 |
| `ov.py` / `ov2.py` | stateOverride 尝试（改 slot3 调小，无效） |
| ⭐ `brute.py` | **暴力搜索裸槽 0-12** —— 发现 slot3 调**大**到 2^200 触发 fee=48000，方向找对了 |
| `findthr.py` | 二分 slot3 临界点，定位 X = 1125899906817966 |

## 决定性实验

| 脚本 | 作用 |
|---|---|
| ⭐ `xorigin.py` | **trace 定位 X 的来源** —— step 215 的 `GAS` 指令。判据就是 `gasleft()` |
| ⭐ `gasproof.py` | **只改 gas limit 的受控实验** —— 临界点 5,024,658，减去入口开销 24,658 = slot3 |
| ⭐ `realproof.py` | **140 笔真实 tx 反验** —— 19 笔收费全部 gasLimit < 5M，零漏报 |
| `cmp.py` | 我的 Solidity 模型 vs 原版字节码逐点比对，40 个采样点 |

## 失败但有价值的尝试

| 脚本 | 作用 |
|---|---|
| `decode.py` | slot1/slot2 字段布局解析（slot2 切分存疑，未完全解出） |
| `verify_model.py` | 用 view call 逐笔重放 325 笔 —— 84.3% 命中但**收费笔全部漏报**，暴露 view call 的 gas 上下文问题 |

---

## 最小复现路径

想验证核心结论，只需两步：

```bash
# 1. 起 anvil
anvil --fork-url https://robinhood.rpc.blxrbdn.com --fork-block-number 33147572 --port 8546

# 2. 跑 gas 临界点实验
~/.v4hook/bin/python scripts/gasproof.py
```

预期输出：临界点 `gas=5024658 → fee=48000` / `gas=5024659 → fee=0`。
