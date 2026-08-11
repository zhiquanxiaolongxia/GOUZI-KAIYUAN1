import pickle, collections
S=pickle.load(open("/tmp/g3s.pkl","rb"))
S.sort(key=lambda s:(s["b"],s["li"]))
TGT="0xa687b664662b96b180a3d4b0f2dc1b0e4d0a0e0e"
# 找出真实 sender 全名
snds=set(s["sender"] for s in S if s["sender"].startswith("0xa687b664"))
TGT=list(snds)[0]
seq=[s for s in S if s["sender"]==TGT]
print("目标 sender:",TGT," 总笔数:",len(seq))
c=collections.Counter(s["fee"] for s in seq)
print("费率分布:",dict(c))
print()
print("="*92)
print("A-10: 该 sender 全部交易时序 —— 看费率升档与什么同步")
print("="*92)
print("%-10s %-4s %-9s %-12s %-8s %-10s %-10s %s"%("block","li","fee","|a0|","tick","Δblock","Δtick","累计"))
prev=None; cum=0
for s in seq:
    db = s["b"]-prev["b"] if prev else 0
    dt = s["tick"]-prev["tick"] if prev else 0
    cum = cum+1 if s["fee"]>0 else 0
    print("%-10d %-4d %-9d %-12d %-8d %-10d %-10d %d"%(s["b"],s["li"],s["fee"],abs(s["a0"]),s["tick"],db,dt,cum))
    prev=s
print()
print("="*92)
print("A-11: 全池所有 swap 的 tick 走势 vs 费率（看是否价格越高罚越狠）")
print("="*92)
buckets=collections.defaultdict(lambda: collections.Counter())
for s in S:
    b = s["tick"]//200*200
    buckets[b][s["fee"]]+=1
for b in sorted(buckets):
    c=buckets[b]
    tot=sum(c.values())
    if tot<3: continue
    print("  tick[%d..%d)  n=%-4d  免费=%-4d 48k=%-3d 95k=%-3d 150k=%-3d"%(
        b,b+200,tot,c[0],c[48000],c[95000],c[150000]))
