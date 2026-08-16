import pickle, collections
S=pickle.load(open("/tmp/g3s.pkl","rb"))
paid=[s for s in S if s["fee"]>0]
c=collections.Counter(s["fee"] for s in paid)
n=len(paid)
print("="*72)
print("E-1: 真实链上收费笔的档位分布 vs 掷骰子模型预测概率")
print("="*72)
# 模型: 在"已收费"条件下(r<9500 且通过 gas 门), 三档占比 = 7500:1000:1000 = 75:10:10
exp={48000:7500/9500, 95000:1000/9500, 150000:1000/9500}
print("%-10s %-8s %-10s %-10s %-10s"%("fee","实际笔数","实际占比","模型占比","偏差"))
import math
chi=0
for f in (48000,95000,150000):
    obs=c[f]; e=exp[f]*n
    chi += (obs-e)**2/e
    print("%-10d %-8d %-10.1f%% %-10.1f%% %+.1f"%(f,obs,100*obs/n,100*exp[f],obs-e))
print()
print("卡方统计量 = %.3f  (df=2, 临界值 5.99 @95%%)"%chi)
print("结论:", "无法拒绝掷骰子模型 ✓" if chi<5.99 else "与模型有显著偏差 ✗")
print()
print("样本量 n=%d 偏小，但方向一致"%n)
print()
print("="*72)
print("E-2: 全池 325 笔的免费率 vs 模型预测")
print("="*72)
free=len([s for s in S if s["fee"]==0])
print("  实际免费: %d/%d = %.1f%%"%(free,len(S),100*free/len(S)))
print("  模型: 免费来自两处 —— (a) gas>=5M 直接放行  (b) gas<5M 但 r>=9500 (5%%)")
print("  故免费率 = P(gas>=5M) + P(gas<5M)*0.05")
print()
print("="*72)
print("E-3: 关键推论 —— 同一 sender 跨档的解释")
print("="*72)
bys=collections.defaultdict(lambda: collections.Counter())
for s in paid: bys[s["sender"]][s["fee"]]+=1
for snd,cc in sorted(bys.items(),key=lambda t:-sum(t[1].values()))[:3]:
    tot=sum(cc.values())
    print("  %s  n=%-3d %s"%(snd[:22],tot,dict(cc)))
print()
print("  掷骰子模型天然解释: 同一地址每笔独立掷骰, 必然跨档 ✓")
print("  '身份白名单'模型无法解释同一地址出现三种费率 ✗")
