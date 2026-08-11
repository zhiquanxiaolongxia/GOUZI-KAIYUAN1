from web3 import Web3
from eth_abi import encode
import pickle
a=Web3(Web3.HTTPProvider("http://127.0.0.1:8546",request_kwargs={"timeout":300}))
H3=Web3.to_checksum_address("0x31Ac5B793C073C7EB15CfC259963CD60004f4080")
PM=Web3.to_checksum_address("0x8366a39CC670B4001A1121B8F6A443A643e40951")
C0=Web3.to_checksum_address("0x5fc5360d0400a0fd4f2af552add042d716f1d168")
C1=Web3.to_checksum_address("0x6245e67affa44a23077f0ea7f981a8dc743a0c47")
SEL=a.keccak(text="beforeSwap(address,(address,address,uint24,int24,address),(bool,int256,uint160),bytes)")[:4]
MIN=4295128740
S=pickle.load(open("/tmp/g3s.pkl","rb"))
TGT=[s for s in S if s["fee"]==150000][0]

def call(gas,amt,sender,z=True):
    d=SEL+encode(["address","(address,address,uint24,int24,address)","(bool,int256,uint160)","bytes"],
     [sender,(C0,C1,0x800000,60,H3),(z,amt,MIN),b""])
    r=a.eth.call({"from":PM,"to":H3,"data":d,"gas":gas})
    return int.from_bytes(r[64:96],"big")&0x3FFFFF

SND=Web3.to_checksum_address(TGT["sender"])
print("="*80)
print("A-12: 复现那 3 笔 150000 —— 用它们的真实参数，在收费 gas 下调用")
print("="*80)
for s in S:
    if s["fee"] in (95000,150000):
        f=call(3_000_000, -abs(s["a0"]), Web3.to_checksum_address(s["sender"]))
        print("  真实 fee=%-8d 复现 fee=%-8d  |a0|=%-12d tick=%d  %s"%(
            s["fee"],f,abs(s["a0"]),s["tick"], "一致" if f==s["fee"] else "<<< 不一致"))

print()
print("="*80)
print("A-13: 决定性检验 —— hook 能否感知池子状态？")
print("  同一笔参数，在不同 fork 块高(=不同池价)下调用，看 fee 是否变化")
print("="*80)
print("  当前 fork 块高:", a.eth.block_number)
print("  (若 hook 无外部调用，则池价对它不可见，fee 只随 gas 变)")
print()
for g in [1_000_000, 3_000_000, 4_999_000]:
    for amt in [-29833301, -442538916, -282303204]:
        f=call(g, amt, SND)
        print("   gas=%-10d |a0|=%-12d fee=%d"%(g,abs(amt),f))
