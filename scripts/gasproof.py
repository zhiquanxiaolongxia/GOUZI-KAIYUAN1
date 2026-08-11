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
x=[y for y in S if y["fee"]>0][0]

def call_gas(gas,amt=None):
    if amt is None: amt=-abs(x["a0"])
    d=SEL+encode(["address","(address,address,uint24,int24,address)","(bool,int256,uint160)","bytes"],
     [Web3.to_checksum_address(x["sender"]),(C0,C1,0x800000,60,H3),(True,amt,MIN),b""])
    r=a.eth.call({"from":PM,"to":H3,"data":d,"gas":gas})
    w=int.from_bytes(r[64:96],"big")
    return w&0x3FFFFF

print("="*76)
print("决定性验证：固定金额，只改 eth_call 的 gas limit")
print("阈值 slot3 = 5,000,000 gas")
print("="*76)
print("%-14s %-10s"%("gas limit","fee"))
for g in [100000,500000,1000000,2000000,3000000,4000000,4900000,4999000,
          5000000,5010000,5100000,6000000,8000000,10000000,20000000,30000000]:
    try:
        f=call_gas(g)
        mark=""
        if f>0: mark="  <<< 收费"
        print("  %-12d %-10d%s"%(g,f,mark))
    except Exception as e:
        print("  %-12d ERR %s"%(g,str(e)[:40]))

print()
print("="*76)
print("二分精确临界点")
print("="*76)
lo,hi=100000,30000000
# 找 fee 从非0变0 的点
def f(g):
    try: return call_gas(g)
    except: return -1
print("  gas=%d -> fee=%d"%(lo,f(lo)))
print("  gas=%d -> fee=%d"%(hi,f(hi)))
while lo<hi-1:
    mid=(lo+hi)//2
    if f(mid)>0: lo=mid
    else: hi=mid
print("  临界: gas=%d -> fee=%d"%(lo,f(lo)))
print("        gas=%d -> fee=%d"%(hi,f(hi)))
print()
print("  slot3 阈值 = 5,000,000")
print("  临界差值   =", hi-5000000, "(call 开销)")
