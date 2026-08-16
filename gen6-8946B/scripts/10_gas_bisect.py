from web3 import Web3
from eth_abi import encode
import json,time
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
SEL="0x575e24b4"
SENDER=Web3.to_checksum_address("0x0000000000000000000000000000000000001234")
MINSQ=4295128740; MAXSQ=1461446703485210103287273052203988822378723970341
OVR=0x400000
def raw(hook,key,zf1,amt,gaslim,sender=SENDER,sq=None):
    if sq is None: sq=MINSQ+1 if zf1 else MAXSQ-1
    d=SEL[2:]+encode(["address","(address,address,uint24,int24,address)","(bool,int256,uint160)","bytes"],
      [sender,(Web3.to_checksum_address(key[0]),Web3.to_checksum_address(key[1]),key[2],key[3],
       Web3.to_checksum_address(key[4])),(zf1,amt,sq),b""]).hex()
    r=rpc(lambda: w3.eth.call({"from":PM,"to":Web3.to_checksum_address(hook),"data":"0x"+d,"gas":gaslim}))
    h=r.hex(); h=h[2:] if h.startswith("0x") else h
    w=[h[i:i+64] for i in range(0,len(h),64)]
    return int(w[2],16)
def fee(*a,**k): 
    v=raw(*a,**k); return v-OVR if v>=OVR else v

kA=pk["A/497D"]; hA=kA[4]
print("="*88);print("S-17: ★ gas 门二分精确定位 (A)");print("="*88,flush=True)
lo,hi=6_010_000,6_050_000
fl=fee(hA,kA,True,-10**16,lo); fh=fee(hA,kA,True,-10**16,hi)
print("  起点 gas=%d fee=%d ; gas=%d fee=%d"%(lo,fl,hi,fh),flush=True)
while lo+1<hi:
    m=(lo+hi)//2
    if fee(hA,kA,True,-10**16,m)==fl: lo=m
    else: hi=m
print("  ★ 分界: gas<=%d -> fee=%d ; gas>=%d -> fee=%d"%(lo,fl,hi,fh),flush=True)
print("  (call gas 与 gasleft 差值 = %d)"%(lo-6_000_000),flush=True)

print()
print("="*88);print("S-18: ★ 金额是否影响费率 (slot6 新机制) — 固定低gas");print("="*88,flush=True)
G=3_000_000
for nm,k in pk.items():
    h=k[4]; print("\n --- %s"%nm,flush=True)
    print("  %-24s %-12s %-10s"%("amountSpecified","fee(raw)","fee%"),flush=True)
    for amt in [-10**12,-10**14,-10**15,-10**16,-10**17,-10**18,-10**19,-10**20,-10**21,
                10**12,10**14,10**16,10**18,10**20]:
        try:
            f=fee(h,k,True,amt,G)
            print("  %-24d %-12d %.4f%%"%(amt,f,f/1e4),flush=True)
        except Exception as e:
            print("  %-24d ERR %s"%(amt,str(e)[:50]),flush=True)

print()
print("="*88);print("S-19: 方向 zeroForOne 是否影响");print("="*88,flush=True)
for nm,k in pk.items():
    h=k[4]
    for zf1 in (True,False):
        try: print("  %s zeroForOne=%-5s -> fee=%d"%(nm,zf1,fee(h,k,zf1,-10**16,G)),flush=True)
        except Exception as e: print("  %s zeroForOne=%-5s ERR %s"%(nm,zf1,str(e)[:50]),flush=True)

print()
print("="*88);print("S-20: sender 是否影响（身份白名单？）");print("="*88,flush=True)
for s in ["0x0000000000000000000000000000000000001234",
          "0x11b4815b9229e3add786b414f5b18e9ec2d39678",
          "0x6A4ADF8B63aBD6E9FeD0d547bfE3419b3ce3d471",
          "0x789150Ad7E5F3b56a6Ce5c71e531a30CCdFAd226"]:
    try: print("  sender=%s -> fee=%d"%(s[:12],fee(hA,kA,True,-10**16,G,sender=Web3.to_checksum_address(s))),flush=True)
    except Exception as e: print("  sender=%s ERR %s"%(s[:12],str(e)[:50]),flush=True)
