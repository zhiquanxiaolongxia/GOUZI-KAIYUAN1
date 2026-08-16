from web3 import Web3
from eth_abi import encode
import json,time,collections,math
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
SEL="0x575e24b4"; OVR=0x400000
MINSQ=4295128740
S2SLOT="0x"+"00"*31+"02"
print("BLK",BLK,flush=True)

def fee(sender,w1,w2,w3_,amt=-10**16,gas=3_000_000,blk=None):
    """w1,w2,w3 = slot2 三个 16bit 权重（低->高）"""
    s2=(w1)|(w2<<16)|(w3_<<32)
    ovr={hA:{"stateDiff":{S2SLOT:"0x%064x"%s2}}}
    d=SEL[2:]+encode(["address","(address,address,uint24,int24,address)","(bool,int256,uint160)","bytes"],
      [Web3.to_checksum_address(sender),
       (Web3.to_checksum_address(kA[0]),Web3.to_checksum_address(kA[1]),kA[2],kA[3],
        Web3.to_checksum_address(kA[4])),(True,amt,MINSQ+1),b""]).hex()
    tx={"from":"0x8366a39CC670B4001A1121B8F6A443A643e40951","to":hA,"data":"0x"+d,"gas":gas}
    x=rpc(lambda: w3.manager.request_blocking("eth_call",[tx,hex(blk if blk else BLK),ovr]))
    hh=x.hex() if hasattr(x,"hex") else str(x)
    hh=hh[2:] if hh.startswith("0x") else hh
    ws=[hh[i:i+64] for i in range(0,len(hh),64)]
    v=int(ws[2],16); return v-OVR if v>=OVR else v

# 费率 -> 档位（八折后）
T={40000:1, 60000:2, 80000:3, 0:0}

def extract_r_via_t1(sender,blk=None):
    """把 w1 从 0 扫到 10000，找 fee 从 tier1 变成非 tier1 的临界 = r
       w1=x 意味着 [0,x) -> tier1。若 r<x 则得 tier1。
       所以最小的使 fee==tier1 的 x 就是 r+1"""
    lo,hi=0,10000
    # 检查单调性前提：w1=10000 全 tier1
    if T.get(fee(sender,10000,0,0,blk=blk),-1)!=1: return None
    if T.get(fee(sender,0,0,0,blk=blk),-1)==1: return None
    while lo+1<hi:
        m=(lo+hi)//2
        if T.get(fee(sender,m,0,0,blk=blk),-1)==1: hi=m
        else: lo=m
    return hi-1     # r

print("="*84);print("S-31: ★ 逼出 r —— 二分 slot2.w1");print("="*84,flush=True)
rs={}
for i in range(12):
    s="0x%040x"%(0x1000+i*7919)
    r=extract_r_via_t1(s)
    rs[s]=r
    print("  sender ...%s  r = %s"%(s[-6:],r),flush=True)

print()
print("="*84);print("S-32: ★★ 过度识别 —— 用 r 预测另外两个边界");print("="*84,flush=True)
print("  规则应为: r<w1 ->T1 ; r<w1+w2 ->T2 ; r<w1+w2+w3 ->T3 ; 否则免费",flush=True)
ok=bad=0
for s,r in list(rs.items())[:8]:
    if r is None: continue
    row=[]
    # 构造若干组权重，预测档位
    tests=[(1000,1000,1000),(3000,3000,3000),(500,500,500),(r,1,1),(r+1,1,1),
           (0,r+1,1),(0,0,r+1),(0,0,r),(2000,4000,2000),(9999,0,0)]
    for w1,w2,w3_ in tests:
        c1,c2,c3=w1,w1+w2,w1+w2+w3_
        pred = 1 if r<c1 else (2 if r<c2 else (3 if r<c3 else 0))
        act  = T.get(fee(s,w1,w2,w3_),-9)
        row.append("✓" if pred==act else "✗(p%d/a%d)"%(pred,act))
        if pred==act: ok+=1
        else: bad+=1
    print("  ...%s r=%-5d %s"%(s[-6:],r," ".join(row)),flush=True)
print("\n  >>> 过度识别命中 %d / %d  = %.1f%%"%(ok,ok+bad,ok*100.0/max(ok+bad,1)),flush=True)
