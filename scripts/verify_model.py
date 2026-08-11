from web3 import Web3
from eth_abi import encode
import pickle, collections
a=Web3(Web3.HTTPProvider("http://127.0.0.1:8546",request_kwargs={"timeout":300}))
H3=Web3.to_checksum_address("0x31Ac5B793C073C7EB15CfC259963CD60004f4080")
PM=Web3.to_checksum_address("0x8366a39CC670B4001A1121B8F6A443A643e40951")
C0=Web3.to_checksum_address("0x5fc5360d0400a0fd4f2af552add042d716f1d168")
C1=Web3.to_checksum_address("0x6245e67affa44a23077f0ea7f981a8dc743a0c47")
SEL=a.keccak(text="beforeSwap(address,(address,address,uint24,int24,address),(bool,int256,uint160),bytes)")[:4]
MIN=4295128740; MAX=1461446703485210103287273052203988822378723970341
S=pickle.load(open("/tmp/g3s.pkl","rb"))

# slot2 正确切分：从最低位起每 24bit 一个字段
s2=int(a.eth.get_storage_at(H3,2).hex(),16)
f0=s2&0xffffff; f1=(s2>>24)&0xffffff; f2=(s2>>48)&0xffffff
print("slot2 从低位起 uint24 字段: %d, %d, %d"%(f0,f1,f2))
print("  0x%x -> %d   0x%x -> %d"%(f0,f0,f1,f1))
print()

# 用真实 sender + 真实参数逐笔重放，与链上实际 fee 比对
print("="*76)
print("逐笔重放 325 笔真实 swap，比对预测 fee vs 链上实际 fee")
print("="*76)
ok=0; bad=0; conf=collections.Counter()
details=[]
for i,x in enumerate(S):
    z = x["a0"] < 0
    amt = -abs(x["a0"]) if z else -abs(x["a1"])
    try:
        d=SEL+encode(["address","(address,address,uint24,int24,address)","(bool,int256,uint160)","bytes"],
            [Web3.to_checksum_address(x["sender"]),(C0,C1,0x800000,60,H3),(z,amt,MIN if z else MAX),b""])
        r=a.eth.call({"from":PM,"to":H3,"data":d},block_identifier=x["b"] if x["b"]<=33147572 else 33147572)
        pred=int.from_bytes(r[64:96],"big")&0x3FFFFF
    except Exception as e:
        pred=-1
    act=x["fee"]
    conf[(act,pred)]+=1
    if pred==act: ok+=1
    else:
        bad+=1
        if len(details)<10: details.append((x["b"],act,pred,x["a0"]))
    if i%50==0: print("  ...%d/%d"%(i,len(S)))

print()
print("命中 %d / %d = %.1f%%"%(ok,len(S),100*ok/len(S)))
print()
print("混淆矩阵 (实际fee, 预测fee) -> 笔数:")
for k,v in sorted(conf.items(),key=lambda t:-t[1])[:15]:
    print("   实际=%-8s 预测=%-8s %d"%(k[0],k[1],v))
print()
print("错例:")
for b,act,pred,a0 in details:
    print("   blk=%d 实际=%d 预测=%d a0=%d"%(b,act,pred,a0))
