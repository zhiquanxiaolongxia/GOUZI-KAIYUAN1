from web3 import Web3
from eth_abi import encode
import pickle, collections
RPC="https://robinhood.rpc.blxrbdn.com"
w3=Web3(Web3.HTTPProvider(RPC,request_kwargs={"timeout":120}))
H3=Web3.to_checksum_address("0x31Ac5B793C073C7EB15CfC259963CD60004f4080")
PM=Web3.to_checksum_address("0x8366a39CC670B4001A1121B8F6A443A643e40951")
C0=Web3.to_checksum_address("0x5fc5360d0400a0fd4f2af552add042d716f1d168")
C1=Web3.to_checksum_address("0x6245e67affa44a23077f0ea7f981a8dc743a0c47")
FEE=0x800000; TS=60
SEL=w3.keccak(text="beforeSwap(address,(address,address,uint24,int24,address),(bool,int256,uint160),bytes)")[:4]
MIN=4295128740; MAX=1461446703485210103287273052203988822378723970341
def call(sender,z,amt,lim,blk,hd=b"",gas=None):
    d=SEL+encode(["address","(address,address,uint24,int24,address)","(bool,int256,uint160)","bytes"],
        [Web3.to_checksum_address(sender),(C0,C1,FEE,TS,H3),(z,amt,lim),hd])
    tx={"from":PM,"to":H3,"data":d}
    if gas: tx["gas"]=gas
    try:
        r=w3.eth.call(tx,block_identifier=blk)
        return int.from_bytes(r[36:68],'big')&0xffffff
    except Exception as e: return "ERR"

S=pickle.load(open("/tmp/g3s.pkl","rb"))
ch=[x for x in S if x["fee"]>0]
x=ch[0]; b=x["b"]; z=(x["a0"]<0); amt=-abs(x["a0"]); sq=x["sq"]
print("基准: blk=%d 实际fee=%d zeroForOne=%s sqrtPrice@swap=%d"%(b,x["fee"],z,sq))
print()
print("="*74)
print("旋钮 1: sqrtPriceLimitX96  (小杨头号嫌疑)")
print("="*74)
cands=[("MIN哨兵",MIN),("MAX哨兵",MAX),("=当前价",sq),
       ("紧-0.01%",int(sq*0.9999)),("紧-0.1%",int(sq*0.999)),("紧-1%",int(sq*0.99)),
       ("紧-5%",int(sq*0.95)),("紧+0.01%",int(sq*1.0001)),("紧+0.1%",int(sq*1.001)),
       ("紧+1%",int(sq*1.01)),("紧+5%",int(sq*1.05))]
for lbl,lim in cands:
    print("  %-12s lim=%-45d fee=%s"%(lbl,lim,call(x["sender"],z,amt,lim,b)))

print()
print("="*74)
print("旋钮 2: hookData")
print("="*74)
for lbl,hd in [("空",b""),("1字节",b"\x01"),("32字节0",bytes(32)),
               ("32字节ff",b"\xff"*32),("abi uint 4800",encode(["uint256"],[4800])),
               ("abi addr",encode(["address"],[Web3.to_checksum_address(x["sender"])]))]:
    print("  %-14s -> fee=%s"%(lbl,call(x["sender"],z,amt,MIN if z else MAX,b,hd)))

print()
print("="*74)
print("旋钮 3: gas limit  (slot3=5,000,000 是否 gas 量纲)")
print("="*74)
for g in [100000,500000,1000000,4999999,5000000,5000001,10000000,30000000]:
    print("  gas=%-10d -> fee=%s"%(g,call(x["sender"],z,amt,MIN if z else MAX,b,b"",g)))
