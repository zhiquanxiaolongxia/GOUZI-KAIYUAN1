from web3 import Web3
from eth_abi import encode
import pickle
a=Web3(Web3.HTTPProvider("http://127.0.0.1:8546",request_kwargs={"timeout":300}))
H3=Web3.to_checksum_address("0x31Ac5B793C073C7EB15CfC259963CD60004f4080")
PM=Web3.to_checksum_address("0x8366a39CC670B4001A1121B8F6A443A643e40951")
C0=Web3.to_checksum_address("0x5fc5360d0400a0fd4f2af552add042d716f1d168")
C1=Web3.to_checksum_address("0x6245e67affa44a23077f0ea7f981a8dc743a0c47")
SEL=a.keccak(text="beforeSwap(address,(address,address,uint24,int24,address),(bool,int256,uint160),bytes)")[:4]
MIN=4295128740
S=pickle.load(open("/tmp/g3s.pkl","rb"))
x=[y for y in S if y["fee"]>0][0]
def hx(n): return "0x"+("%064x"%n)
def setslot(s,v): a.provider.make_request("anvil_setStorageAt",[H3,hx(s),hx(v)])
def call(amt=None,z=True):
    if amt is None: amt=-abs(x["a0"])
    d=SEL+encode(["address","(address,address,uint24,int24,address)","(bool,int256,uint160)","bytes"],
     [Web3.to_checksum_address(x["sender"]),(C0,C1,0x800000,60,H3),(z,amt,MIN),b""])
    r=a.eth.call({"from":PM,"to":H3,"data":d})
    w=int.from_bytes(r[64:96],"big")
    return w&0x3FFFFF

o3=int(a.eth.get_storage_at(H3,3).hex(),16)
print("slot3 原值 = %d (0x%x)"%(o3,o3))
print()
print("="*76)
print("二分 slot3 阈值：找到 fee 从 0 跳到 48000 的临界点")
print("="*76)
lo,hi=5000000,2**200
while lo<hi-1:
    mid=(lo+hi)//2
    setslot(3,mid)
    f=call()
    if f==0: lo=mid
    else: hi=mid
setslot(3,lo); f_lo=call()
setslot(3,hi); f_hi=call()
print("  临界: slot3=%d -> fee=%d"%(lo,f_lo))
print("        slot3=%d -> fee=%d"%(hi,f_hi))
print("  hi = 0x%x"%hi)
print("  hi 是否 2^n:", [n for n in range(256) if 2**n==hi] or "no")
print("  hi/1e18 = %.6f"%(hi/1e18))
print()
print("="*76)
print("固定 slot3=2^200，扫金额 -> 看是否出现多档费率")
print("="*76)
setslot(3,2**200)
for v in [1,1000,10**6,10**9,10**12,10**15,10**18,10**21]:
    print("  amt=-%-20d fee=%d"%(v,call(-v)))
print()
print("--- 同时扫 slot1/slot2 (费率档/阈值) 与金额的关系 ---")
o1=int(a.eth.get_storage_at(H3,1).hex(),16)
o2=int(a.eth.get_storage_at(H3,2).hex(),16)
print("  slot1=0x%x"%o1)
print("  slot2=0x%x"%o2)
setslot(3,o3)
print()
print("已还原 slot3 =",int(a.eth.get_storage_at(H3,3).hex(),16))
