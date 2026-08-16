from web3 import Web3
from eth_abi import encode
import pickle, json
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
    [{"from":PM,"to":H3,"data":"0x"+d.hex()},"latest",{"disableMemory":True}])
logs=r["result"]["structLogs"]

# 正确读栈：EVM 栈顶在数组末尾。LT 弹出 top(a) 与 next(b)，计算 a < b
print("="*74)
print("精确解析所有比较指令 (LT/GT/SLT/SGT/EQ) —— 栈序修正版")
print("="*74)
CMP={"LT":"<","GT":">","SLT":"<(s)","SGT":">(s)","EQ":"=="}
for i,l in enumerate(logs):
    if l["op"] in CMP:
        st=l["stack"]
        a1=int(st[-1],16); b1=int(st[-2],16)
        res=logs[i+1]["stack"][-1] if i+1<len(logs) else "?"
        print("  step%-5d %-5s  a=%-24d %s b=%-24d -> %s"%(
            i,l["op"],a1,CMP[l["op"]],b1,res))

print()
print("="*74)
print("所有 SLOAD 读到的值")
print("="*74)
for i,l in enumerate(logs):
    if l["op"]=="SLOAD":
        slot=int(l["stack"][-1],16)
        val=int(logs[i+1]["stack"][-1],16) if i+1<len(logs) else 0
        print("  step%-5d slot=0x%x"%(i,slot))
        print("            value=%d (0x%x)"%(val,val))
