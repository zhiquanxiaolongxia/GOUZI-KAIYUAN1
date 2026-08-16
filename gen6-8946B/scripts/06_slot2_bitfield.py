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
pk=json.load(open("/tmp/poolkeys.json"))
hA=Web3.to_checksum_address(pk["A/497D"][4])
hB=Web3.to_checksum_address(pk["B/7266"][4])
BLK=rpc(lambda: w3.eth.block_number)-10
print("BLK",BLK,flush=True)
for nm,h in [("A",hA),("B",hB)]:
    for s in range(8):
        v=int(rpc(lambda: w3.eth.get_storage_at(h,s,block_identifier=BLK)).hex(),16)
        print("  %s slot%d = 0x%x  (%d)"%(nm,s,v,v),flush=True)
    print(flush=True)

# feeForRoll 探针：不受骰子干扰的纯映射
SELF="0x14724809"
def froll(h,r,ovr=None):
    d=SELF[2:]+encode(["uint16"],[r]).hex()
    tx={"to":h,"data":"0x"+d}
    args=[tx,hex(BLK)]+([ovr] if ovr else [])
    x=rpc(lambda: w3.manager.request_blocking("eth_call",args))
    hh=x.hex() if hasattr(x,"hex") else str(x)
    hh=hh[2:] if hh.startswith("0x") else hh
    return int(hh,16)

def curve(h,ovr=None,step=250):
    pts=[]; prev=None
    for r in range(0,10000,step):
        v=froll(h,r,ovr)
        if v!=prev: pts.append((r,v)); prev=v
    return pts

print("="*84);print("S-29: feeForRoll 原始曲线（纯映射探针）");print("="*84,flush=True)
for nm,h in [("A",hA),("B",hB)]:
    print("  %s: %s"%(nm,curve(h)),flush=True)

print()
print("="*84);print("S-30: ★ 爆破 slot2 位布局 —— 逐 16bit 字段单独改，看曲线拐点怎么动");print("="*84,flush=True)
s2=int(rpc(lambda: w3.eth.get_storage_at(hA,2,block_identifier=BLK)).hex(),16)
print("  A 原 slot2 = 0x%x"%s2,flush=True)
def ov2(v): return {hA:{"stateDiff":{"0x"+"00"*31+"02":"0x%064x"%v}}}
for shift in range(0,256,16):
    fld=(s2>>shift)&0xffff
    if fld==0: continue
    nv=(s2 & ~(0xffff<<shift)) | (777<<shift)
    c=curve(hA,ov2(nv))
    print("  bit%-3d 原值%-6d -> 改成777 后曲线 %s"%(shift,fld,c),flush=True)
