from web3 import Web3
from eth_abi import encode
import json,time,collections
URL="https://robinhood.rpc.blxrbdn.com"
def mk(): return Web3(Web3.HTTPProvider(URL,request_kwargs={"timeout":45}))
w3=mk()
def rpc(fn):
    global w3
    for a in range(5):
        try: return fn()
        except Exception as e:
            if a==4: raise
            time.sleep(2); w3=mk()
PM=Web3.to_checksum_address("0x8366a39CC670B4001A1121B8F6A443A643e40951")
pk=json.load(open("/tmp/poolkeys.json"))
SEL="0x575e24b4"; OVR=0x400000
MINSQ=4295128740; MAXSQ=1461446703485210103287273052203988822378723970341
BLK=rpc(lambda: w3.eth.block_number)-10
print("★ BLK =",BLK,flush=True)
kA=pk["A/497D"]; hA=Web3.to_checksum_address(kA[4])
kB=pk["B/7266"]; hB=Web3.to_checksum_address(kB[4])
G=3_000_000

def call(hook,key,zf1,amt,sender,ovr=None,gas=G):
    sq=MINSQ+1 if zf1 else MAXSQ-1
    d=SEL[2:]+encode(["address","(address,address,uint24,int24,address)","(bool,int256,uint160)","bytes"],
      [Web3.to_checksum_address(sender),
       (Web3.to_checksum_address(key[0]),Web3.to_checksum_address(key[1]),key[2],key[3],
        Web3.to_checksum_address(key[4])),(zf1,amt,sq),b""]).hex()
    tx={"from":PM,"to":Web3.to_checksum_address(hook),"data":"0x"+d,"gas":gas}
    args=[tx,BLK]+([ovr] if ovr else [])
    r=rpc(lambda: w3.manager.request_blocking("eth_call",args))
    h=r.hex() if hasattr(r,"hex") else str(r)
    h=h[2:] if h.startswith("0x") else h
    w=[h[i:i+64] for i in range(0,len(h),64)]
    v=int(w[2],16); return v-OVR if v>=OVR else v

def sweep(hook,key,zf1,amt,n=120,ovr=None):
    c=collections.Counter()
    for i in range(n):
        s="0x%040x"%(0x1000+i*7919)
        try: c[call(hook,key,zf1,amt,s,ovr)]+=1
        except Exception as e: c["ERR"]+=1
    return c
def show(t,c):
    tot=sum(v for k,v in c.items() if k!="ERR")
    print("  %s (n=%d):"%(t,tot),flush=True)
    for f,n in sorted(c.items(),key=lambda x:(str(x[0]))):
        pct=n*100.0/max(tot,1)
        print("     fee=%-9s %3d  %5.1f%%   (%.2f%%费率)"%(f,n,pct,(f/1e4) if isinstance(f,int) else 0),flush=True)

print("="*88);print("S-25: 120 个 sender 扫骰子分布 @固定块");print("="*88,flush=True)
show("A exactIn(-1e16)",sweep(hA,kA,True,-10**16))
show("A exactOut(+1e16)",sweep(hA,kA,True,10**16))
show("B exactIn(-1e16)",sweep(hB,kB,True,-10**16))

print()
print("="*88);print("S-26: ★★ stateOverride slot6 —— 折扣因果实验 (A)");print("="*88,flush=True)
def ov6(val): return {hA:{"stateDiff":{"0x"+"00"*31+"06":"0x%064x"%val}}}
for lbl,val in [("原值 0x7d001 (en=1,disc=2000)",0x7d001),
                ("disc=0    -> 应=100%档位",0x00001),
                ("disc=5000 -> 应=50%",0x1388_01),
                ("disc=9000 -> 应=10%",0x2328_01),
                ("enabled=0 (关开关)",0x7d000),
                ("全 0",0x0)]:
    c=sweep(hA,kA,True,-10**16,n=60,ovr=ov6(val))
    tot=sum(v for k,v in c.items() if k!="ERR")
    vals=sorted([k for k in c if k!="ERR"])
    print("  slot6=0x%-8x %-32s -> 费率集合 %s"%(val,lbl,vals),flush=True)

print()
print("="*88);print("S-27: ★★ stateOverride slot3 —— gas 门因果实验 (A)");print("="*88,flush=True)
def ov3(val): return {hA:{"stateDiff":{"0x"+"00"*31+"03":"0x%064x"%val}}}
for th in [6_000_000,3_000_000,1_000_000,10_000_000,0]:
    try:
        lo=call(hA,kA,True,-10**16,"0x%040x"%0x1234,ovr=ov3(th),gas=2_000_000)
        hi=call(hA,kA,True,-10**16,"0x%040x"%0x1234,ovr=ov3(th),gas=20_000_000)
        print("  阈值=%-11d  gas2M -> %-8s   gas20M -> %-8s"%(th,lo,hi),flush=True)
    except Exception as e:
        print("  阈值=%-11d ERR %s"%(th,str(e)[:60]),flush=True)

print()
print("="*88);print("S-28: ★★ stateOverride slot1 —— tier 费率因果实验 (A)");print("="*88,flush=True)
s1=int(rpc(lambda: w3.eth.get_storage_at(hA,1)).hex(),16)
print("  原 slot1 = 0x%064x"%s1,flush=True)
def setf(t1,t2,t3):
    v=s1
    v&=~(0xffffff<<160); v|=(t1<<160)
    v&=~(0xffffff<<184); v|=(t2<<184)
    v&=~(0xffffff<<208); v|=(t3<<208)
    return {hA:{"stateDiff":{"0x"+"00"*31+"01":"0x%064x"%v}}}
for t1,t2,t3 in [(50000,75000,100000),(10000,20000,30000),(1000,2000,3000),(200000,300000,400000)]:
    c=sweep(hA,kA,True,-10**16,n=60,ovr=setf(t1,t2,t3))
    vals=sorted([k for k in c if k!="ERR"])
    exp=sorted(set([0,int(t1*0.8),int(t2*0.8),int(t3*0.8)]))
    print("  tier=(%d,%d,%d) -> 实测%s  预期(x0.8)%s  %s"%(t1,t2,t3,vals,exp,"✓匹配" if vals==exp else "✗不符"),flush=True)
