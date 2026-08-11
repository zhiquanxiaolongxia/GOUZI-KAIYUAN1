from web3 import Web3
from eth_abi import encode
import pickle, json
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

tr=a.provider.make_request("debug_traceCall",[{"from":PM,"to":H3,"data":"0x"+d.hex(),"gas":hex(3_000_000)},"latest",{"disableStorage":False,"disableMemory":True,"disableStack":False}])
logs=tr["result"]["structLogs"]
print("总 step:",len(logs))

# 1. 所有外部调用类 opcode
print("\n"+"="*80)
print("B-1: 外部调用类 opcode（验证'无外部调用'是否真的成立）")
print("="*80)
ext=[l for l in logs if l["op"] in ("CALL","STATICCALL","DELEGATECALL","CALLCODE","EXTCODESIZE","EXTCODECOPY","BALANCE","EXTCODEHASH")]
if ext:
    for l in ext: print("  step%-6d %s  depth=%d"%(l["pc"],l["op"],l["depth"]))
else:
    print("  确认: 零外部调用")

# 2. 所有 SLOAD 及其读到的值
print("\n"+"="*80)
print("B-2: 全部 SLOAD（hook 读了哪些槽）")
print("="*80)
seen=set()
for i,l in enumerate(logs):
    if l["op"]=="SLOAD":
        st=l["stack"]
        key=st[-1] if st else "?"
        val=logs[i+1]["stack"][-1] if i+1<len(logs) and logs[i+1]["stack"] else "?"
        if (key,val) in seen: continue
        seen.add((key,val))
        print("  step%-6d SLOAD key=0x%s"%(l["pc"],key[-20:]))
        print("                    val=0x%s  (%d)"%(val[-20:],int(val,16)))

# 3. 环境类 opcode
print("\n"+"="*80)
print("B-3: 环境/上下文类 opcode（hook 从哪取运行时信息）")
print("="*80)
envops={}
for i,l in enumerate(logs):
    if l["op"] in ("GAS","TIMESTAMP","NUMBER","GASPRICE","ORIGIN","BASEFEE","BLOCKHASH","COINBASE","DIFFICULTY","PREVRANDAO","CHAINID","SELFBALANCE","CALLER","CALLVALUE"):
        v=logs[i+1]["stack"][-1] if i+1<len(logs) and logs[i+1]["stack"] else "?"
        envops.setdefault(l["op"],[]).append((l["pc"],v))
for op,vs in envops.items():
    print("  %-12s x%d"%(op,len(vs)))
    for pc,v in vs[:4]:
        print("      pc=%-6d -> 0x%s (%d)"%(pc,v[-16:],int(v,16)))
