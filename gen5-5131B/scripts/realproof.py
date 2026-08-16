from web3 import Web3
import pickle, collections, statistics
w3=Web3(Web3.HTTPProvider("https://robinhood.rpc.blxrbdn.com",request_kwargs={"timeout":180}))
S=pickle.load(open("/tmp/g3s.pkl","rb"))

print("="*76)
print("用真实链上 tx 验证模型：gasLimit < 5,000,000 -> 收费")
print("="*76)
txs={}
for x in S:
    txs.setdefault(x["tx"],[]).append(x)

rows=[]
n=0
for tx,items in txs.items():
    n+=1
    if n>140: break
    try:
        t=w3.eth.get_transaction(tx)
        gl=t["gas"]
        fee=max(i["fee"] for i in items)
        rows.append((tx,gl,fee))
    except Exception as e:
        pass

print("取到 %d 笔 tx 的 gasLimit"%len(rows))
print()
charged=[r for r in rows if r[2]>0]
free=[r for r in rows if r[2]==0]
print("收费 %d 笔, 免费 %d 笔"%(len(charged),len(free)))
print()
if charged:
    g=[r[1] for r in charged]
    print("收费笔 gasLimit: min=%d max=%d 中位=%d"%(min(g),max(g),int(statistics.median(g))))
    print("   <5,000,000 的占比: %d/%d = %.1f%%"%(sum(1 for v in g if v<5000000),len(g),100*sum(1 for v in g if v<5000000)/len(g)))
if free:
    g=[r[1] for r in free]
    print("免费笔 gasLimit: min=%d max=%d 中位=%d"%(min(g),max(g),int(statistics.median(g))))
    print("   >=5,000,000 的占比: %d/%d = %.1f%%"%(sum(1 for v in g if v>=5000000),len(g),100*sum(1 for v in g if v>=5000000)/len(g)))

print()
print("="*76)
print("按模型预测 (gasLimit<5e6 => 收费) 的混淆矩阵")
print("="*76)
tp=sum(1 for r in rows if r[1]<5000000 and r[2]>0)
fp=sum(1 for r in rows if r[1]<5000000 and r[2]==0)
fn=sum(1 for r in rows if r[1]>=5000000 and r[2]>0)
tn=sum(1 for r in rows if r[1]>=5000000 and r[2]==0)
print("           预测收费   预测免费")
print("实际收费   %-10d %-10d"%(tp,fn))
print("实际免费   %-10d %-10d"%(fp,tn))
print()
print("准确率 = %.1f%%"%(100*(tp+tn)/max(1,len(rows))))

print()
print("样例:")
for tx,gl,fee in rows[:20]:
    print("  gasLimit=%-10d fee=%-8d %s"%(gl,fee,tx[:20]))
