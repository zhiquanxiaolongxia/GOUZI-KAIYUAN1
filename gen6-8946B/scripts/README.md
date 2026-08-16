# 脚本索引

按**证据价值**排序，不是按执行顺序。⭐ 越多越关键。

## ⭐⭐⭐ 决定性脚本（结论全靠这两个）

### `07_overidentification.py` — 过度识别 80/80
本轮最硬的证据。做两件事：
1. **逼出 r**：二分 `slot2.w1`，找费率跳出 tier1 的临界点 = 该 sender 的隐藏随机数 `r`
2. **过度识别检验**：用这**一个** `r` 去预测另外 10 组权重配置下的档位

一个参数解释多个独立边界 → 蒙不出来。含贴边测试 `(r,1,1)` vs `(r+1,1,1)`，差 1 翻档。
**输出**：`raw-output/r14.out`

### `08_uniformity_avalanche.py` — 均匀性 + 雪崩 + 双路径
三个独立检验：
1. **双路径交叉**：扫 `w1` 和扫 `w2` 两条独立路径逼出的 r 必须相同（8/8 通过）
2. **卡方 + KS**：80 个 r 的分布均匀性 → 哈希取模的指纹（χ²=4.25，KS 通过）
3. **种子成分探测**：改金额 1 wei / 改方向 / 改区块，看 r 是否雪崩

**输出**：`raw-output/r15.out`

---

## ⭐⭐ 因果实验

### `05_causal_stateoverride.py` — stateOverride 改 storage 看输出
改 slot6（折扣）/ slot1（费率档）/ slot3（gas 门），验证每个槽的因果作用。
这是「因果」而非「相关」的分界线。**输出**：`raw-output/r12.out`

### `06_slot2_bitfield.py` — slot2 位布局爆破
逐 16bit 字段单独改成 777，看 `feeForRoll` 曲线拐点怎么移动 → 解出三段累积权重结构。
**输出**：`raw-output/r13.out`

---

## ⭐ 基础侦察

| 脚本 | 作用 | 输出 |
|---|---|---|
| `01_poolkey_bruteforce.py` | 本地爆破 poolKey（枚举 tickSpacing+fee 匹配已知 poolId）。**受控实验的钥匙**，秒级出结果 | — |
| `02_getters_feeforroll.py` | selector 爆破找 getter + `feeForRoll(uint16)` 全曲线 | `r5.out` |
| `03_gas_gate.py` | gas 门实证（注意正确 selector 含 sender） | `r9.out` |
| `04_fixed_block_control.py` | 固定区块受控实验 —— **拆穿「金额决定费率」假信号的那一个** | `r11.out` |
| `09_event_decode.py` | 事件字段解码，发现 `data[0]` 恒定 10417 | `r6.out` |
| `10_gas_bisect.py` | gas 分界二分 → 6,024,219 / 6,024,220 | `r10.out` |

---

## 💀 失败但有价值的尝试

### 「连续费率曲线」的错误路线（已从结论中删除）
早期把事件 `data[0]` 当 1e6 精度费率读，统计出 0.579%/0.804%/1.099% 三档，
并据此得出「按金额分档的连续曲线」结论 —— **全错**。
该字段 33/35 条恒为 10417。**恒定值是解码错误的警报，不是变量。**

### `04_fixed_block_control.py` 之前的版本
不固定 `block_identifier`，扫金额看到费率乱变，误判「金额影响费率」。
真相是每次 call 打在新块上，骰子重掷。这个坑值得单独记住。

---

## 环境

```bash
python3 -m venv .venv
./.venv/bin/pip install web3 eth-abi eth-utils
```
RPC: `https://robinhood.rpc.blxrbdn.com`（chainId 4663）
脚本内的 `PM` 常量是 PoolManager 地址，`eth_call` 的 `from` 必须是它，否则 `onlyPoolManager` 拦截。

⚠️ 脚本命名避开 Python 标准库名（`dis` / `types` / `code` / `token` / `json` / `select`），
在 cwd 建同名文件会 shadow 标准库，导致同目录其他脚本 import 崩溃。
