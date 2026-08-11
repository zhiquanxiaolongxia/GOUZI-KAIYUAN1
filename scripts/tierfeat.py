import pickle, collections, statistics
S=pickle.load(open("/tmp/g3s.pkl","rb"))
S.sort(key=lambda s:(s["b"],s["li"]))
paid=[s for s in S if s["fee"]>0]
g1=[s for s in paid if s["fee"]==48000]
g2=[s for s in paid if s["fee"]==95000]
g3=[s for s in paid if s["fee"]==150000]
free=[s for s in S if s["fee"]==0]

def fix(v,bits=128):
    return v-(1<<bits) if v>=(1<<(bits-1)) else v

def stat(name,g,f):
    vs=[f(s) for s in g]
    vs=[v for v in vs if v is not None]
    if not vs: return
    print("  %-10s n=%-3d  min=%-16s med=%-16s max=%-16s"%(name,len(vs),
        f"{min(vs):.4g}",f"{statistics.median(vs):.4g}",f"{max(vs):.4g}"))

print("="*80)
print("A-6: 三档收费笔 vs 免费笔 —— 逐特征对比，找 tier2/tier3 的判据")
print("="*80)

feats=[
 ("|a0| 金额",     lambda s: abs(s["a0"])),
 ("|a1| 金额",     lambda s: abs(s["a1"])),
 ("liquidity",     lambda s: s["liq"]),
 ("tick",          lambda s: s["tick"]),
 ("sqrtPrice",     lambda s: s["sq"]),
 ("logIndex",      lambda s: s["li"]),
]
for fname,fn in feats:
    print("\n[%s]"%fname)
    stat("免费",free,fn); stat("48000",g1,fn); stat("95000",g2,fn); stat("150000",g3,fn)

print()
print("="*80)
print("A-7: 高档笔的 |a0| / liquidity 比值（=这笔占池子多大比例，冲击力代理量）")
print("="*80)
def impact(s):
    return abs(s["a0"])/s["liq"]*1e18 if s["liq"] else None
stat("免费",free,impact); stat("48000",g1,impact); stat("95000",g2,impact); stat("150000",g3,impact)

print()
print("="*80)
print("A-8: 高档笔明细（95000 / 150000 共 8 笔）")
print("="*80)
print("%-10s %-4s %-14s %-22s %-10s %-8s"%("block","li","fee","|a0|","tick","sender"))
for s in sorted(g2+g3,key=lambda x:x["b"]):
    print("%-10d %-4d %-14d %-22d %-10d %s"%(s["b"],s["li"],s["fee"],abs(s["a0"]),s["tick"],s["sender"][:14]))

print()
print("="*80)
print("A-9: 同 sender 是否跨档（若某 sender 既有 48000 又有 150000 => 与身份无关）")
print("="*80)
bys=collections.defaultdict(lambda: collections.Counter())
for s in paid: bys[s["sender"]][s["fee"]]+=1
for snd,c in sorted(bys.items(),key=lambda t:-sum(t[1].values())):
    if len(c)>1 or sum(c.values())>=3:
        print("  %s  %s"%(snd[:20],dict(c)))
