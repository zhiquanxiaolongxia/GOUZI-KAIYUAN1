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
SENDER=Web3.to_checksum_address("0x0000000000000000000000000000000000001234")
MINSQ=4295128740; MAXSQ=1461446703485210103287273052203988822378723970341
BLK=rpc(lambda: w3.eth.block_number)-8      # ★ 固定区块，骰子恒定
print("★ 固定区块 BLK =",BLK,flush=True)
def fee(hook,key,zf1,amt,gaslim,sender=SENDER,blk=None):
    sq=MINSQ+1 if zf1 else MAXSQ-1
    d=SEL[2:]+encode(["address","(address,address,uint24,int24,address)","(bool,int256,uint160)","bytes"],
      [sender,(Web3.to_checksum_address(key[0]),Web3.to_checksum_address(key[1]),key[2],key[3],
       Web3.to_checksum_address(key[4])),(zf1,amt,sq),b""]).hex()
    r=rpc(lambda: w3.eth.call({"from":PM,"to":Web3.to_checksum_address(hook),"data":"0x"+d,
        "gas":gaslim},block_identifier=blk if blk is not None else BLK))
    h=r.hex(); h=h[2:] if h.startswith("0x") else h
    w=[h[i:i+64] for i in range(0,len(h),64)]
    v=int(w[2],16); return v-OVR if v>=OVR else v

kA=pk["A/497D"]; hA=kA[4]; kB=pk["B/7266"]; hB=kB[4]
G=3_000_000
print("="*88);print("S-21: 同参数重复 10 次 @固定块 —— 验证确定性");print("="*88,flush=True)
vs=[fee(hA,kA,True,-10**16,G) for _ in range(10)]
print("  A: %s   全同=%s"%(vs,len(set(vs))==1),flush=True)

print()
print("="*88);print("S-22: ★ 金额影响（固定块，骰子恒定）");print("="*88,flush=True)
for nm,k in [("A",kA),("B",kB)]:
    h=k[4]; out=[]
    for amt in [-10**10,-10**12,-10**14,-10**15,-10**16,-10**17,-10**18,-10**19,-10**20,-10**21,-10**22]:
        try: out.append((amt,fee(h,k,True,amt,G)))
        except Exception as e: out.append((amt,"ERR"))
    print("  %s exactIn(负):"%nm,flush=True)
    for a,f in out: print("     %-24d %s"%(a,f),flush=True)
    print("     >>> 唯一值:",set(x[1] for x in out),flush=True)
    out2=[]
    for amt in [10**10,10**12,10**14,10**16,10**18,10**20,10**22]:
        try: out2.append((amt,fee(h,k,True,amt,G)))
        except Exception as e: out2.append((amt,"ERR"))
    print("  %s exactOut(正):"%nm,flush=True)
    for a,f in out2: print("     %-24d %s"%(a,f),flush=True)
    print("     >>> 唯一值:",set(x[1] for x in out2),flush=True)

print()
print("="*88);print("S-23: ★ 方向 / sender（固定块）");print("="*88,flush=True)
for nm,k in [("A",kA),("B",kB)]:
    for zf1 in (True,False):
        print("  %s zf1=%-5s fee=%s"%(nm,zf1,fee(k[4],k,zf1,-10**16,G)),flush=True)
for s in ["0x0000000000000000000000000000000000001234",
          "0x11b4815b9229e3add786b414f5b18e9ec2d39678",
          "0x6A4ADF8B63aBD6E9FeD0d547bfE3419b3ce3d471",
          "0x789150Ad7E5F3b56a6Ce5c71e531a30CCdFAd226",
          "0x000000000022D473030F116dDEE9F6B43aC78BA3"]:
    print("  A sender=%s fee=%s"%(s[:14],fee(hA,kA,True,-10**16,G,sender=Web3.to_checksum_address(s))),flush=True)

print()
print("="*88);print("S-24: ★ 跨 40 个连续块，同参数 —— 骰子分布 vs feeForRoll 权重");print("="*88,flush=True)
for nm,k in [("A",kA),("B",kB)]:
    c=collections.Counter()
    for i in range(40):
        try: c[fee(k[4],k,True,-10**16,G,blk=BLK-i)]+=1
        except Exception: c["ERR"]+=1
    tot=sum(v for x,v in c.items() if x!="ERR")
    print("  %s 分布(n=%d):"%(nm,tot),flush=True)
    for f,n in sorted(c.items(),key=lambda x:(str(x[0]))):
        print("     fee=%-9s %2d 次  %.1f%%"%(f,n,n*100.0/max(tot,1)),flush=True)
