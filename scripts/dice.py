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

def trace(amt,gas=3_000_000,sender=SND):
    d=SEL+encode(["address","(address,address,uint24,int24,address)","(bool,int256,uint160)","bytes"],
     [sender,(C0,C1,0x800000,60,H3),(True,amt,MIN),b""])
    tr=a.provider.make_request("debug_traceCall",[{"from":PM,"to":H3,"data":"0x"+d.hex(),"gas":hex(gas)},"latest",
        {"disableStorage":True,"disableMemory":True,"disableStack":False}])
    logs=tr["result"]["structLogs"]
    r=None; fee=None
    for i,l in enumerate(logs):
        if l["op"]=="MOD":
            st=l["stack"]
            if len(st)>=2 and int(st[-2],16)==10000:
                r=int(logs[i+1]["stack"][-1],16)
    ret=tr["result"].get("returnValue","")
    if ret:
        fee=int(ret[128:192],16)&0x3FFFFF if len(ret)>=192 else None
    return r,fee

print("="*80)
print("D-1: 验证'掷骰子'模型 —— r = keccak(...) % 10000")
print("  阈值(slot2): thrA=7500  thrB=1000  thrC=1000")
print("  假设: r 落在不同区间 -> 不同费率档")
print("="*80)
print("%-16s %-8s %-10s"%("|a0|","r","fee"))
rows=[]
import random
tests=[1_000_000,10_000_000,29_833_301,50_000_000,100_000_000,150_000_000,
       200_000_000,282_303_204,300_000_000,442_538_916,500_000_000,1_000_000_000]
tests+=[random.randint(1_000_000,900_000_000) for _ in range(28)]
for amt in tests:
    try:
        r,f=trace(-amt)
        rows.append((amt,r,f))
        print("%-16d %-8s %-10s"%(amt,r,f))
    except Exception as e:
        print("%-16d ERR %s"%(amt,str(e)[:40]))

print()
print("="*80)
print("D-2: 按 r 值排序，找区间边界")
print("="*80)
ok=[x for x in rows if x[1] is not None and x[2] is not None]
ok.sort(key=lambda t:t[1])
for amt,r,f in ok:
    print("  r=%-6d fee=%-8d  |a0|=%d"%(r,f,amt))
print()
import collections
byfee=collections.defaultdict(list)
for amt,r,f in ok: byfee[f].append(r)
print("每档的 r 范围:")
for f,rs in sorted(byfee.items()):
    print("   fee=%-8d n=%-3d  r∈[%d, %d]"%(f,len(rs),min(rs),max(rs)))
