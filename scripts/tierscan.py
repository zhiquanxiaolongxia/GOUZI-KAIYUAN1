from web3 import Web3
from eth_abi import encode
import pickle
a=Web3(Web3.HTTPProvider("http://127.0.0.1:8546",request_kwargs={"timeout":300}))
H3=Web3.to_checksum_address("0x31Ac5B793C073C7EB15CfC259963CD60004f4080")
PM=Web3.to_checksum_address("0x8366a39CC670B4001A1121B8F6A443A643e40951")
C0=Web3.to_checksum_address("0x5fc5360d0400a0fd4f2af552add042d716f1d168")
C1=Web3.to_checksum_address("0x6245e67affa44a23077f0ea7f981a8dc743a0c47")
SEL=a.keccak(text="beforeSwap(address,(address,address,uint24,int24,address),(bool,int256,uint160),bytes)")[:4]
MIN=4295128740; MAX=1461446703485210103287273052203988822378723970341
S=pickle.load(open("/tmp/g3s.pkl","rb"))
x=[y for y in S if y["fee"]>0][0]
SENDER=Web3.to_checksum_address(x["sender"])

def call(gas,amt=None,z=True,sender=SENDER,hd=b""):
    if amt is None: amt=-abs(x["a0"])
    d=SEL+encode(["address","(address,address,uint24,int24,address)","(bool,int256,uint160)","bytes"],
     [sender,(C0,C1,0x800000,60,H3),(z,amt,MIN if z else MAX),hd])
    r=a.eth.call({"from":PM,"to":H3,"data":d,"gas":gas})
    return int.from_bytes(r[64:96],"big")&0x3FFFFF

print("="*76)
print("A-1: 全 gas 区间细扫，找 tier2(95000)/tier3(150000) 是否自然出现")
print("阈值 slot3=5,000,000  入口开销 24,658")
print("="*76)
found={}
# 粗扫
prev=None
for g in range(50000, 5200000, 25000):
    f=call(g)
    found.setdefault(f,[]).append(g)
    if prev is not None and f!=prev:
        print("  >>> 跳变 gas~%d: %d -> %d"%(g,prev,f))
    prev=f
print()
print("粗扫结果 (gas 50k~5.2M, 步长 25k):")
for f,gs in sorted(found.items()):
    print("   fee=%-8d 出现 %-4d 次  gas范围 [%d, %d]"%(f,len(gs),min(gs),max(gs)))
print()
print("="*76)
print("A-2: 极低 gas 区间细扫 (可能 tier 与剩余 gas 分档相关)")
print("="*76)
found2={}
for g in range(21000, 300000, 2000):
    try:
        f=call(g)
        found2.setdefault(f,[]).append(g)
    except Exception as e:
        found2.setdefault("OOG",[]).append(g)
for f,gs in sorted(found2.items(),key=lambda t:str(t[0])):
    print("   fee=%-8s 出现 %-4d 次  gas范围 [%d, %d]"%(f,len(gs),min(gs),max(gs)))
