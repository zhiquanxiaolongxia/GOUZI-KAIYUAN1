import pickle, collections, statistics
from web3 import Web3
w3=Web3()
raw=pickle.load(open("/tmp/g3.pkl","rb"))
SWAP="0x"+w3.keccak(text="Swap(bytes32,address,int128,int128,uint160,uint128,int24,uint24)").hex()
def fx(v,bits):
    v&=(1<<bits)-1
    return v-(1<<bits) if v>=1<<(bits-1) else v
S=[]
for r in raw:
    if r["t"][0]!=SWAP: continue
    dd=bytes.fromhex(r["d"]); ws=[int.from_bytes(dd[i:i+32],'big') for i in range(0,len(dd),32)]
    S.append(dict(b=r["b"],li=r["li"],tx=r["tx"],sender="0x"+r["t"][2][-40:],
                  a0=fx(ws[0],128),a1=fx(ws[1],128),sq=ws[2],liq=ws[3],
                  tick=fx(ws[4],24),fee=ws[5]))
S.sort(key=lambda x:(x["b"],x["li"]))
print("三代池 swap 总数",len(S))
c=collections.Counter(x["fee"] for x in S)
print("\n=== 费率分布（三代配置 4.8/9.5/15%）===")
for f,n in sorted(c.items()):
    print("  fee %6.2f%%  n=%-4d (%.1f%%)"%(f/10000.0,n,100.0*n/len(S)))
print("\n=== 按 sender ===")
by=collections.defaultdict(collections.Counter)
for x in S: by[x["sender"]][x["fee"]]+=1
for a,cc in sorted(by.items(),key=lambda kv:-sum(kv[1].values())):
    t=sum(cc.values()); z=cc.get(0,0)
    d=' '.join('%.1f%%:%d'%(f/10000.0,n) for f,n in sorted(cc.items()) if f)
    print("  %s n=%-4d 免费%.0f%%  %s"%(a,t,100.0*z/t,d or '-'))
print("\n=== amount/L 按档 ===")
r2=collections.defaultdict(list)
for x in S:
    if x["liq"]>0: r2[x["fee"]].append(abs(x["a0"])/x["liq"])
for f in sorted(r2):
    v=sorted(r2[f]); print("  fee %6.2f%% n=%-4d |a0|/L中位=%.6g"%(f/10000.0,len(v),statistics.median(v)))
pickle.dump(S,open("/tmp/g3s.pkl","wb"))
print("\n=== 前 20 笔明细 ===")
for x in S[:20]:
    print("  blk=%d fee=%-7d a0=%-22d liq=%-20d tick=%d"%(x["b"],x["fee"],x["a0"],x["liq"],x["tick"]))
