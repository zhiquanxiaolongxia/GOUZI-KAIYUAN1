import pickle, collections
S=pickle.load(open("/tmp/g3s.pkl","rb"))
print("="*76)
print("A-3: 真实链上 325 笔 swap 的费率分布 —— tier2/tier3 到底存不存在")
print("="*76)
c=collections.Counter(s["fee"] for s in S)
for f,n in sorted(c.items()):
    print("   fee=%-8d %4d 笔  %5.1f%%"%(f,n,100*n/len(S)))
print()
paid=[s for s in S if s["fee"]>0]
print("收费笔总数:",len(paid))
print()
# 按时间看费率是否随 owner 调参而变
print("="*76)
print("A-4: 收费笔按区块排序，看费率是否随时间切换（=owner 调参而非动态分档）")
print("="*76)
paid.sort(key=lambda s:(s["b"],s.get("li",0)))
print("%-10s %-8s %-12s"%("block","fee","备注"))
prev=None
for s in paid:
    mark=""
    if prev is not None and s["fee"]!=prev:
        mark="  <<< 费率切换"
    print("%-10d %-8d %s"%(s["b"],s["fee"],mark))
    prev=s["fee"]
print()
# 费率的区块区间
print("="*76)
print("A-5: 每个费率档覆盖的区块区间（若区间不重叠 => 是配置切换，不是动态分档）")
print("="*76)
byfee=collections.defaultdict(list)
for s in paid: byfee[s["fee"]].append(s["b"])
for f,bs in sorted(byfee.items()):
    print("   fee=%-8d  区块 [%d .. %d]  共 %d 笔"%(f,min(bs),max(bs),len(bs)))
print()
ivs=[(min(bs),max(bs),f) for f,bs in byfee.items()]
ivs.sort()
overlap=False
for i in range(len(ivs)-1):
    if ivs[i][1] >= ivs[i+1][0]:
        overlap=True
        print("   !! 区间重叠: fee=%d [%d,%d] 与 fee=%d [%d,%d]"%(ivs[i][2],ivs[i][0],ivs[i][1],ivs[i+1][2],ivs[i+1][0],ivs[i+1][1]))
print("区间是否重叠:", "是 => 同期存在多档，可能是动态分档" if overlap else "否 => 各档时间上互斥，强烈指向 owner 调参")
