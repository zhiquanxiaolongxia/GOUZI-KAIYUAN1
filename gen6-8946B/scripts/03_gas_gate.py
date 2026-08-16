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
SIG="beforeSwap(address,(address,address,uint24,int24,address),(bool,int256,uint160),bytes)"
SEL=w3.keccak(text=SIG)[:4].hex()
if not SEL.startswith("0x"): SEL="0x"+SEL
print("beforeSwap selector:",SEL,flush=True)
SENDER=Web3.to_checksum_address("0x0000000000000000000000000000000000001234")
MINSQ=4295128740

def call(hook,key,zf1,amt,gaslim,sender=SENDER):
    d=SEL[2:]+encode(["address","(address,address,uint24,int24,address)","(bool,int256,uint160)","bytes"],
      [sender,(Web3.to_checksum_address(key[0]),Web3.to_checksum_address(key[1]),key[2],key[3],
       Web3.to_checksum_address(key[4])),(zf1,amt,MINSQ+1),b""]).hex()
    return rpc(lambda: w3.eth.call({"from":PM,"to":Web3.to_checksum_address(hook),"data":"0x"+d,"gas":gaslim}))

def parse(r):
    h=r.hex(); h=h[2:] if h.startswith("0x") else h
    w=[h[i:i+64] for i in range(0,len(h),64)]
    return len(w), (w[0][:8] if w else "?"), (int(w[2],16) if len(w)>2 else None)

print("="*88);print("S-16: ★ gas 门受控实验");print("="*88,flush=True)
for nm,k in pk.items():
    hook=k[4]; print("\n --- %s hook=%s"%(nm,hook),flush=True)
    for g in [30_000_000,10_000_000,7_000_000,6_100_000,6_050_000,6_010_000,
              6_000_000,5_900_000,5_000_000,2_000_000,500_000]:
        try:
            n,s4,fee=parse(call(hook,k,True,-10**16,g))
            print("   gas=%-11d words=%-3d sel=%s fee=%-9s (%.4f%%)"%(g,n,s4,fee,(fee or 0)/1e4),flush=True)
        except Exception as e:
            print("   gas=%-11d ERR %s"%(g,str(e)[:60]),flush=True)
