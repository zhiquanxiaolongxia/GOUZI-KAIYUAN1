from web3 import Web3
from eth_abi import encode
import pickle
a=Web3(Web3.HTTPProvider("http://127.0.0.1:8547",request_kwargs={"timeout":300}))
H3=Web3.to_checksum_address("0x31Ac5B793C073C7EB15CfC259963CD60004f4080")
PM=Web3.to_checksum_address("0x8366a39CC670B4001A1121B8F6A443A643e40951")
C0=Web3.to_checksum_address("0x5fc5360d0400a0fd4f2af552add042d716f1d168")
C1=Web3.to_checksum_address("0x6245e67affa44a23077f0ea7f981a8dc743a0c47")
SEL=a.keccak(text="beforeSwap(address,(address,address,uint24,int24,address),(bool,int256,uint160),bytes)")[:4]
MIN=4295128740
S=pickle.load(open("/tmp/g3s.pkl","rb"))
# 33285337 li=27 是那笔 150000
T=[s for s in S if s["b"]==33285337 and s["fee"]==150000][0]
SND=Web3.to_checksum_address(T["sender"])

def call(gas,amt,sender=SND,z=True):
    d=SEL+encode(["address","(address,address,uint24,int24,address)","(bool,int256,uint160)","bytes"],
     [sender,(C0,C1,0x800000,60,H3),(z,amt,MIN),b""])
    r=a.eth.call({"from":PM,"to":H3,"data":d,"gas":gas})
    return int.from_bytes(r[64:96],"big")&0x3FFFFF

print("="*84)
print("A-14: 决定性实验 —— fork 到出事前一块 33285336，复现那笔 150000")
print("  目标: blk 33285337 li=27  fee=150000  |a0|=%d"%abs(T["a0"]))
print("  若 fee 仍=48000 => hook 看不见池子状态，150000 另有来源")
print("  若 fee  =150000 => hook 确实感知池价，小杨的偏离说成立")
print("="*84)
for g in [500_000, 1_000_000, 2_000_000, 3_000_000, 4_000_000, 5_000_000, 5_024_658]:
    try:
        f=call(g, -abs(T["a0"]))
        print("   gas=%-10d fee=%-8d %s"%(g,f,"<<< 命中 150000!" if f==150000 else ""))
    except Exception as e:
        print("   gas=%-10d ERR %s"%(g,str(e)[:50]))

print()
print("对照: 同块高下扫不同金额 (gas=3M)")
for amt in [1_000_000, 10_000_000, 29_833_301, 100_000_000, 282_303_204, 442_538_916, 1_000_000_000]:
    try:
        f=call(3_000_000, -amt)
        print("   |a0|=%-14d fee=%d"%(amt,f))
    except Exception as e:
        print("   |a0|=%-14d ERR"%amt)

print()
print("="*84)
print("A-15: 读取该块高下 hook 的 storage —— 配置是否被 owner 改过")
print("="*84)
for i in range(6):
    v=a.eth.get_storage_at(H3,i)
    print("  slot%d  0x%s"%(i,v.hex()))
