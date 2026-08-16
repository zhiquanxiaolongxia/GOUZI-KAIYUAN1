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
MAX=1461446703485210103287273052203988822378723970341
S=pickle.load(open("/tmp/g3s.pkl","rb"))
x=[y for y in S if y["fee"]>0][0]
SENDER=Web3.to_checksum_address(x["sender"])
OVERRIDE_FLAG=1<<22

def call(amt,z=True,sender=SENDER,lim=None,hd=b""):
    if lim is None: lim=MIN if z else MAX
    d=SEL+encode(["address","(address,address,uint24,int24,address)","(bool,int256,uint160)","bytes"],
        [sender,(C0,C1,0x800000,60,H3),(z,amt,lim),hd])
    r=a.eth.call({"from":PM,"to":H3,"data":d})
    w2=int.from_bytes(r[64:96],"big")
    return w2 & 0x3FFFFF, bool(w2 & OVERRIDE_FLAG), w2   # 低22位=fee, bit22=override

print("="*76)
print("修正解析后：word2 低22位 = lpFee, bit22 = OVERRIDE_FLAG")
print("="*76)
f,ov,raw=call(-abs(x["a0"]))
print("  基线: fee=%d override=%s raw=0x%x"%(f,ov,raw))
print()
print("="*76)
print("重扫金额 (之前因解析错全部作废)")
print("="*76)
for v in [1000,100000,1000000,4999999,5000000,5000001,10**7,10**8,10**9,10**12,10**15,10**18]:
    f,ov,raw=call(-v)
    print("  amt=-%-18d fee=%-8d override=%s"%(v,f,ov))
print()
print("--- exactOut (正数) ---")
for v in [1000,1000000,5000000,10**9,10**15]:
    f,ov,raw=call(v)
    print("  amt=+%-18d fee=%-8d override=%s"%(v,f,ov))
