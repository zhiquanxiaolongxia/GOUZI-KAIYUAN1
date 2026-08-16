from web3 import Web3
from eth_abi import encode
import pickle
RPC="https://robinhood.rpc.blxrbdn.com"
w3=Web3(Web3.HTTPProvider(RPC,request_kwargs={"timeout":120}))
H3=Web3.to_checksum_address("0x31Ac5B793C073C7EB15CfC259963CD60004f4080")
PM=Web3.to_checksum_address("0x8366a39CC670B4001A1121B8F6A443A643e40951")
# 从 Initialize 事件读到的真实 poolKey
C0=Web3.to_checksum_address("0x5fc5360d0400a0fd4f2af552add042d716f1d168")
C1=Web3.to_checksum_address("0x6245e67affa44a23077f0ea7f981a8dc743a0c47")
FEE=0x800000; TS=60
SEL=w3.keccak(text="beforeSwap(address,(address,address,uint24,int24,address),(bool,int256,uint160),bytes)")[:4]
MIN=4295128740; MAX=1461446703485210103287273052203988822378723970341

# 先自检：算出的 poolId 必须等于真实 poolId
pid=w3.keccak(encode(["address","address","uint24","int24","address"],[C0,C1,FEE,TS,H3]))
REAL="bd317ebfd767c06e3723fa1bccf48a6ac6931bf4c94a23a0669e21472b714d47"
print("poolId 自检: 算出 %s"%pid.hex())
print("            真实 %s"%REAL)
print("            %s"%("✅ 一致" if pid.hex()==REAL else "❌ 不一致——poolKey 仍然错"))
print()

def build(sender,z,amt,lim,hd=b""):
    return SEL+encode(["address","(address,address,uint24,int24,address)","(bool,int256,uint160)","bytes"],
        [Web3.to_checksum_address(sender),(C0,C1,FEE,TS,H3),(z,amt,lim),hd])
def call(sender,z,amt,lim,blk,hd=b""):
    try:
        r=w3.eth.call({"from":PM,"to":H3,"data":build(sender,z,amt,lim,hd)},block_identifier=blk)
        raw=int.from_bytes(r[36:68],'big')
        return raw&0xffffff, raw
    except Exception as e: return ("ERR",str(e)[:60])

S=pickle.load(open("/tmp/g3s.pkl","rb"))
ch=[x for x in S if x["fee"]>0]
fr=[x for x in S if x["fee"]==0]
x=ch[0]; b=x["b"]

print("="*74)
print("用【正确 poolKey】重放被罚交易 blk=%d 实际fee=%d"%(b,x["fee"]))
print("="*74)
z=(x["a0"]<0)
f,raw=call(x["sender"],z,-abs(x["a0"]),MIN if z else MAX,b)
print("  默认哨兵 lim: fee=%s  raw=0x%x"%(f,raw if isinstance(raw,int) else 0))
f2,_=call(x["sender"],z,-abs(x["a0"]),MIN if z else MAX,b-1)
print("  前一区块    : fee=%s"%f2)
