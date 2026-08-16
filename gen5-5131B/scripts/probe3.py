from web3 import Web3
from eth_abi import encode
RPC="https://robinhood.rpc.blxrbdn.com"
w3=Web3(Web3.HTTPProvider(RPC,request_kwargs={"timeout":120}))
H3=Web3.to_checksum_address("0x31Ac5B793C073C7EB15CfC259963CD60004f4080")
PM=Web3.to_checksum_address("0x8366a39CC670B4001A1121B8F6A443A643e40951")
C0=Web3.to_checksum_address("0x0bd7d308f8e1639fab988df18a8011f41eacad73")
C1=Web3.to_checksum_address("0x5fc5360d0400a0fd4f2af552add042d716f1d168")
SEL=w3.keccak(text="beforeSwap(address,(address,address,uint24,int24,address),(bool,int256,uint160),bytes)")[:4]
MIN=4295128740; MAX=1461446703485210103287273052203988822378723970341
def build(sender,z,amt,hd=b""):
    return SEL+encode(["address","(address,address,uint24,int24,address)","(bool,int256,uint160)","bytes"],
        [Web3.to_checksum_address(sender),(C0,C1,0x800000,60,H3),(z,amt,MIN if z else MAX),hd])
def call(sender,z,amt,blk,hd=b""):
    try:
        r=w3.eth.call({"from":PM,"to":H3,"data":build(sender,z,amt,hd)},block_identifier=blk)
        return int.from_bytes(r[36:68],'big')&0xffffff
    except Exception as e: return "ERR"
def gas(sender,z,amt,blk,hd=b""):
    try:
        return w3.eth.estimate_gas({"from":PM,"to":H3,"data":build(sender,z,amt,hd)},block_identifier=blk)
    except Exception as e: return -1

import pickle
S=pickle.load(open("/tmp/g3s.pkl","rb"))
ch=[x for x in S if x["fee"]>0]

print("="*72)
print("A. hookData 探针：被罚交易的 hookData 是不是非空？")
print("="*72)
# 找出这些 tx 的实际 hookData 无法直读，改测：空 hookData vs 伪造 hookData 是否改变 fee
x=ch[0]; b=x["b"]; z=(x["a0"]<0)
for hd in [b"", b"\x01", b"\xff"*32, bytes.fromhex("deadbeef")]:
    print("  hookData=%-12s -> fee=%s"%(hd.hex()[:10] or "(empty)", call(x["sender"],z,-abs(x["a0"]),b,hd)))

print()
print("="*72)
print("B. gas 探针：不同金额下 beforeSwap 的 gas 是否分叉")
print("   (gas 不同 = 走了不同分支 = 有条件判断)")
print("="*72)
for blk,lbl in [(b,"被罚区块"),(b-1,"前一区块")]:
    gs=[]
    for a in [10**3,10**5,10**7,abs(x["a0"]),10**9,10**11]:
        gs.append((a,gas(x["sender"],z,-a,blk),call(x["sender"],z,-a,blk)))
    print(" %s blk=%d"%(lbl,blk))
    for a,g,f in gs: print("    amt=%-14d gas=%-8d fee=%s"%(a,g,f))
