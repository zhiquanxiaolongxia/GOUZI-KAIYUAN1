from eth_abi import encode
from eth_utils import keccak
A="0x497dfc4a2a7aa7b5479cb8191b495a7e405500c4"
B="0x7266ba24c6da4a8e6ae931b61728625377ee00c4"
P_A="717fd7ee0f0725ea031dc19e60b040b5dd21fdcc94cb3e871bf0e27b020effa1"
P_B="a53aed8eb6f4c8a2c5d990c261868f45d2b2f10b13f1b14924ef5a6e614f2a28"
t3=546752078524806549824452760637979359403954000232
TOK="0x%040x"%t3
print("t3 token =",TOK)
NATIVE="0x"+"00"*20
cands=[NATIVE,TOK,"0x5fc5360d5c7dd2d0f8b1dd2e2b0b6f6bd1cfd168"]
print()
print("爆破 poolKey: currency0/1 + fee=0x800000 + tickSpacing")
found={}
for hook,pid,nm in [(A,P_A,"A/497D"),(B,P_B,"B/7266")]:
    ok=False
    for c0 in cands:
        for c1 in cands:
            if c0.lower()==c1.lower(): continue
            for fee in (0x800000,0,3000,500,10000,100):
                for ts in list(range(1,501))+[1000,2000,32767,60,200,10]:
                    k=keccak(encode(["address","address","uint24","int24","address"],[c0,c1,fee,ts,hook]))
                    if k.hex()==pid:
                        print("  ★ %s 命中!  c0=%s c1=%s fee=0x%x ts=%d"%(nm,c0,c1,fee,ts))
                        found[nm]=(c0,c1,fee,ts,hook); ok=True; break
                if ok: break
            if ok: break
        if ok: break
    if not ok: print("  %s 未命中"%nm)
import json
json.dump({k:list(v) for k,v in found.items()},open("/tmp/poolkeys.json","w"))
print("saved",found)
