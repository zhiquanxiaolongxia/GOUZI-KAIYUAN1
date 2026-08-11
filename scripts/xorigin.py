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

d=SEL+encode(["address","(address,address,uint24,int24,address)","(bool,int256,uint160)","bytes"],
 [Web3.to_checksum_address(x["sender"]),(C0,C1,0x800000,60,H3),(True,-abs(x["a0"]),MIN),b""])
r=a.provider.make_request("debug_traceCall",
    [{"from":PM,"to":H3,"data":"0x"+d.hex()},"latest",{"disableMemory":False,"disableStack":False}])
logs=r["result"]["structLogs"]

# X 第一次出现在栈上的位置 = 它被算出来的地方
X=1125899906817966
first=None
for i,l in enumerate(logs):
    st=l.get("stack",[])
    if any(int(s,16)==X for s in st):
        first=i; break
print("X=%d 首次出现在 step %d"%(X,first))
print()
print("="*76)
print("X 诞生前后 40 条指令")
print("="*76)
for i in range(max(0,first-40), min(len(logs),first+6)):
    l=logs[i]
    st=l.get("stack",[])
    top=[hex(int(s,16)) for s in st[-4:]][::-1] if st else []
    mark="  <<< X 出现" if i==first else ""
    print("%-5d %-14s %s%s"%(i,l["op"],top,mark))
