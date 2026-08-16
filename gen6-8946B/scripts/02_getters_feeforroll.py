from web3 import Web3
import time
URL="https://robinhood.rpc.blxrbdn.com"
def mk(): return Web3(Web3.HTTPProvider(URL,request_kwargs={"timeout":30}))
w3=mk()
def rpc(fn):
    global w3
    for a in range(6):
        try: return fn()
        except Exception as e:
            if a==5: raise
            time.sleep(2*(a+1)); w3=mk()
A=Web3.to_checksum_address("0x497DFc4A2a7aA7b5479Cb8191b495a7E405500c4")
B=Web3.to_checksum_address("0x7266BA24C6Da4A8E6Ae931B61728625377eE00c4")

NAMED={"0x9a50c628":"tierOneFee","0x08ac6289":"tierTwoFee","0x9d951b3b":"tierThreeFee",
"0x5a6c72d0":"defaultFee","0xe1a45218":"BPS_DENOMINATOR","0x8fd0b484":"?(=6e6, gas门?)"}
print("="*80);print("S-10: 真 getter 值 (A vs B)");print("="*80)
for sel,nm in NAMED.items():
    row=[]
    for ad in (A,B):
        try:
            v=int(rpc(lambda: w3.eth.call({"to":ad,"data":sel})).hex(),16)
        except Exception as e: v="ERR"
        row.append(v)
    print("  %-22s %-12s A=%-12s B=%-12s"%(nm,sel,row[0],row[1]))

print()
print("="*80);print("S-11: ★ feeForRoll(uint16) 全曲线 —— 骰子->费率映射");print("="*80)
for nm,ad in [("A",A),("B",B)]:
    print("  --- %s"%nm)
    prev=None; changes=[]
    vals={}
    for x in range(0,10000,100):
        try: v=int(rpc(lambda: w3.eth.call({"to":ad,"data":"0x14724809"+"%064x"%x})).hex(),16)
        except Exception: v=None
        vals[x]=v
        if prev is not None and v!=prev: changes.append((x,prev,v))
        prev=v
    # 二分细化边界
    fine=[]
    for x,pv,nv in changes:
        lo,hi=x-100,x
        while lo+1<hi:
            m=(lo+hi)//2
            try: mv=int(rpc(lambda: w3.eth.call({"to":ad,"data":"0x14724809"+"%064x"%m})).hex(),16)
            except Exception: break
            if mv==pv: lo=m
            else: hi=m
        fine.append((hi,pv,nv))
    print("     r=0 -> %s (%.2f%%)"%(vals[0],(vals[0] or 0)/1e6*100))
    for bd,pv,nv in fine:
        print("     r>=%-6d 由 %-8s 变为 %-8s   (%.2f%% -> %.2f%%)"%(bd,pv,nv,pv/1e6*100,nv/1e6*100))
    
    # 概率汇总
    bounds=[0]+[b for b,_,_ in fine]+[10000]
    print("     >>> 概率分布:")
    for k in range(len(bounds)-1):
        lo,hi=bounds[k],bounds[k+1]
        f=vals[0] if k==0 else fine[k-1][2]
        print("         [%5d,%5d)  p=%5.2f%%   fee=%-8s (%.2f%%)"%(lo,hi,(hi-lo)/100.0,f,f/1e6*100))
