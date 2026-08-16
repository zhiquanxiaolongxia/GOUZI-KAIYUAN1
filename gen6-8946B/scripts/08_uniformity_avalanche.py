from web3 import Web3
from eth_abi import encode
import json,time,math,collections
URL="https://robinhood.rpc.blxrbdn.com"
def mk(): return Web3(Web3.HTTPProvider(URL,request_kwargs={"timeout":45}))
w3=mk()
def rpc(fn):
    global w3
    for a in range(5):
        try: return fn()
        except Exception as e:
            if a==4: raise
            time.sleep(1.5); w3=mk()
pk=json.load(open("/tmp/poolkeys.json"))
kA=pk["A/497D"]; hA=Web3.to_checksum_address(kA[4])
BLK=rpc(lambda: w3.eth.block_number)-12
SEL="0x575e24b4"; OVR=0x400000; MINSQ=4295128740
S2="0x"+"00"*31+"02"
PM="0x8366a39CC670B4001A1121B8F6A443A643e40951"
print("BLK",BLK,flush=True)
T={40000:1,60000:2,80000:3,0:0}

def fee(sender,w1,w2,w3_,amt=-10**16,blk=None,z=True):
    s2=w1|(w2<<16)|(w3_<<32)
    ovr={hA:{"stateDiff":{S2:"0x%064x"%s2}}}
    d=SEL[2:]+encode(["address","(address,address,uint24,int24,address)","(bool,int256,uint160)","bytes"],
      [Web3.to_checksum_address(sender),
       (Web3.to_checksum_address(kA[0]),Web3.to_checksum_address(kA[1]),kA[2],kA[3],
        Web3.to_checksum_address(kA[4])),
       (z,amt,MINSQ+1 if z else 1461446703485210103287273052203988822378723970341)]).hex() if False else \
      SEL[2:]+encode(["address","(address,address,uint24,int24,address)","(bool,int256,uint160)","bytes"],
      [Web3.to_checksum_address(sender),
       (Web3.to_checksum_address(kA[0]),Web3.to_checksum_address(kA[1]),kA[2],kA[3],
        Web3.to_checksum_address(kA[4])),
       (z,amt,MINSQ+1 if z else 1461446703485210103287273052203988822378723970341),b""]).hex()
    tx={"from":PM,"to":hA,"data":"0x"+d,"gas":3_000_000}
    x=rpc(lambda: w3.manager.request_blocking("eth_call",[tx,hex(blk or BLK),ovr]))
    hh=x.hex() if hasattr(x,"hex") else str(x)
    hh=hh[2:] if hh.startswith("0x") else hh
    ws=[hh[i:i+64] for i in range(0,len(hh),64)]
    v=int(ws[2],16); return v-OVR if v>=OVR else v

def getr(sender,amt=-10**16,blk=None,z=True,route=1):
    """route1: 二分 w1。 route2: w1=0 二分 w2（独立路径，交叉验证）"""
    lo,hi=0,10000
    if route==1:
        f=lambda m: T.get(fee(sender,m,0,0,amt,blk,z),-1)==1
    else:
        f=lambda m: T.get(fee(sender,0,m,0,amt,blk,z),-1)==2
    if not f(10000): return None
    if f(0): return None
    while lo+1<hi:
        m=(lo+hi)//2
        if f(m): hi=m
        else: lo=m
    return hi-1

print("="*84);print("S-33: ★ 双路径交叉验证 —— 两种独立二分应得同一个 r");print("="*84,flush=True)
agree=dis=0
for i in range(10):
    s="0x%040x"%(0x5000+i*104729)
    a=getr(s,route=1); b=getr(s,route=2)
    st="✓" if a==b else "✗"
    if a==b: agree+=1
    else: dis+=1
    print("  ...%s  route1=%-5s route2=%-5s %s"%(s[-6:],a,b,st),flush=True)
print("  >>> 一致 %d/%d"%(agree,agree+dis),flush=True)

print()
print("="*84);print("S-34: ★★ r 的分布均匀性检验（哈希取模的指纹）");print("="*84,flush=True)
rs=[]
for i in range(80):
    s="0x%040x"%(0x90000+i*15485863)
    r=getr(s)
    if r is not None: rs.append(r)
print("  样本 n=%d  min=%d max=%d mean=%.1f (理论均值4999.5)"%(len(rs),min(rs),max(rs),sum(rs)/len(rs)),flush=True)
# 卡方 10 桶
b=[0]*10
for r in rs: b[min(r//1000,9)]+=1
e=len(rs)/10.0
chi=sum((x-e)**2/e for x in b)
print("  十桶计数: %s"%b,flush=True)
print("  卡方=%.2f  df=9  (临界值 16.92@p0.05, 21.67@p0.01)"%chi,flush=True)
print("  → %s"%("均匀，符合 keccak%%10000" if chi<16.92 else "偏离均匀，模型存疑"),flush=True)
srt=sorted(rs); n=len(srt)
ks=max(max(abs((i+1)/n-v/10000.0),abs(i/n-v/10000.0)) for i,v in enumerate(srt))
crit=1.36/math.sqrt(n)
print("  KS D=%.4f  临界=%.4f@p0.05 → %s"%(ks,crit,"通过" if ks<crit else "拒绝"),flush=True)

print()
print("="*84);print("S-35: ★ r 是否随入参重掷（种子成分探测）");print("="*84,flush=True)
s="0x%040x"%0xBEEF
base=getr(s)
print("  基准 sender=..beef amt=-1e16 zeroForOne=True  r=%s"%base,flush=True)
for lbl,kw in [("金额 -2e16",{"amt":-2*10**16}),("金额 -1e16+1",{"amt":-10**16+1}),
               ("方向反转",{"z":False}),("区块 -1",{"blk":BLK-1}),("区块 -2",{"blk":BLK-2})]:
    v=getr(s,**kw)
    print("  %-16s r=%-6s %s"%(lbl,v,"← 变了(进种子)" if v!=base else "← 没变"),flush=True)
print("  重复同参 3 次:",[getr(s) for _ in range(3)],flush=True)
