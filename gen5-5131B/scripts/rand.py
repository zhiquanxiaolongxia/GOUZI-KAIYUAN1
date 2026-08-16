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
T=[s for s in S if s["b"]==33285337 and s["fee"]==150000][0]
SND=Web3.to_checksum_address(T["sender"])
d=SEL+encode(["address","(address,address,uint24,int24,address)","(bool,int256,uint160)","bytes"],
 [SND,(C0,C1,0x800000,60,H3),(True,-abs(T["a0"]),MIN),b""])

tr=a.provider.make_request("debug_traceCall",[{"from":PM,"to":H3,"data":"0x"+d.hex(),"gas":hex(3_000_000)},"latest",{"disableStorage":True,"disableMemory":False,"disableStack":False}])
logs=tr["result"]["structLogs"]

# 找 BLOCKHASH 之后的运算链
idx=[i for i,l in enumerate(logs) if l["op"]=="BLOCKHASH"][0]
print("="*84)
print("C-1: BLOCKHASH 之后的完整运算链（看伪随机数怎么构造）")
print("="*84)
for i in range(idx-6, min(idx+70,len(logs))):
    l=logs[i]
    st=l.get("stack",[])
    top=("0x"+st[-1][-24:]) if st else ""
    top2=("0x"+st[-2][-24:]) if len(st)>1 else ""
    print("  %-5d %-14s top=%-26s top2=%s"%(i,l["op"],top,top2))

# 找 KECCAK256/SHA3
print()
print("="*84)
print("C-2: KECCAK256 调用点（伪随机的核心）")
print("="*84)
for i,l in enumerate(logs):
    if l["op"] in ("KECCAK256","SHA3"):
        out=logs[i+1]["stack"][-1] if i+1<len(logs) else "?"
        print("  step %-5d %s -> 0x%s"%(i,l["op"],out))

# 找 MOD / AND 等取模运算
print()
print("="*84)
print("C-3: MOD/AND/DIV 运算（取模分档的证据）")
print("="*84)
for i,l in enumerate(logs):
    if l["op"] in ("MOD","SMOD","AND","DIV","SHR") and i>idx-20:
        st=l.get("stack",[])
        if len(st)>=2:
            av,bv=int(st[-1],16),int(st[-2],16)
            out=int(logs[i+1]["stack"][-1],16) if i+1<len(logs) and logs[i+1]["stack"] else None
            if out is not None and (bv<100000 or av<100000):
                print("  step %-5d %-8s  %d , %d  -> %d"%(i,l["op"],av,bv,out))
