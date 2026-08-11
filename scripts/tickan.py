import pickle, statistics, collections, math
S=pickle.load(open("/tmp/g3s.pkl","rb"))
# 用上一笔 swap 的收盘 sqrtPrice 作为"参考价"，看本笔开盘偏离
prev=None
rows=[]
for x in S:
    if prev is None:
        rows.append((x,None,None)); prev=x; continue
    # 本笔的"入场价"无法直接得，但可用上一笔结束价与本笔结束价比较tick漂移
    dt=x["tick"]-prev["tick"]
    db=x["b"]-prev["b"]
    rows.append((x,dt,db))
    prev=x
print("="*74)
print("A. 距上一笔的 tick 漂移 vs 费率  (tick差 = 价格对数变化)")
print("="*74)
g=collections.defaultdict(list)
for x,dt,db in rows:
    if dt is not None: g[x["fee"]].append(abs(dt))
for f in sorted(g):
    v=sorted(g[f])
    print("  fee %6.2f%% n=%-4d |Δtick|中位=%-8d p25=%-7d p75=%-8d"%(
        f/10000.0,len(v),statistics.median(v),v[len(v)//4],v[3*len(v)//4]))

print()
print("="*74)
print("B. 关键检验：阈值 7500/1000/1000 若是 tick 单位?")
print("   三代阈值 thr1=7500 thr2=1000 thr3=1000")
print("="*74)
# 检查是否 |Δtick| 超过某值就罚
for TH in [100,250,500,1000,2000,5000,7500]:
    a=sum(1 for x,dt,db in rows if dt is not None and abs(dt)>=TH and x["fee"]>0)
    b=sum(1 for x,dt,db in rows if dt is not None and abs(dt)>=TH)
    c=sum(1 for x,dt,db in rows if dt is not None and abs(dt)<TH and x["fee"]>0)
    print("  |Δtick|>=%-6d : 命中%d/%d笔被罚  漏网%d笔"%(TH,a,b,c))

print()
print("="*74)
print("C. 单笔自身造成的 tick 冲击 (本笔 tick - 上一笔 tick 同向?)")
print("="*74)
g2=collections.defaultdict(list)
for x,dt,db in rows:
    if db is not None and db>0: g2[x["fee"]].append(db)
for f in sorted(g2):
    v=sorted(g2[f]); print("  fee %6.2f%% 距上笔块数中位=%d"%(f/10000.0,statistics.median(v)))

print()
print("="*74)
print("D. 组合：间隔>=N 块 AND ... 能不能 100% 分离")
print("="*74)
for N in [5,8,50,100,200,290]:
    tp=sum(1 for x,dt,db in rows if db is not None and db>=N and x["fee"]>0)
    fp=sum(1 for x,dt,db in rows if db is not None and db>=N and x["fee"]==0)
    fn=sum(1 for x,dt,db in rows if db is not None and db<N and x["fee"]>0)
    print("  间隔>=%-5d : 被罚命中%-4d 误报(免费却>=N)%-4d 漏网%-4d"%(N,tp,fp,fn))
