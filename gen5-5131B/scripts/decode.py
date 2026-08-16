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
def call(amt,z=True):
    d=SEL+encode(["address","(address,address,uint24,int24,address)","(bool,int256,uint160)","bytes"],
     [Web3.to_checksum_address(x["sender"]),(C0,C1,0x800000,60,H3),(z,amt,MIN),b""])
    r=a.eth.call({"from":PM,"to":H3,"data":d})
    return int.from_bytes(r[64:96],"big")&0x3FFFFF

o3=int(a.eth.get_storage_at(H3,3).hex(),16)

# 解 slot1 / slot2 的字段布局
s1=int(a.eth.get_storage_at(H3,1).hex(),16)
s2=int(a.eth.get_storage_at(H3,2).hex(),16)
print("="*76); print("slot1 / slot2 字段拆解 (小端槽内打包，从低位起)"); print("="*76)
def unpack(v,name,widths):
    print("  %s = 0x%x"%(name,v))
    off=0
    for w in widths:
        f=(v>>off)&((1<<w)-1)
        if f: print("     bit%-4d w%-4d = %-12d (0x%x)"%(off,w,f,f))
        off+=w
unpack(s1,"slot1",[24]*10)
unpack(s2,"slot2",[24]*10)

print()
print("="*76); print("X = 1125899906817966 的物理含义"); print("="*76)
X=1125899906817966
print("  X          =",X)
print("  X hex      = 0x%x"%X)
print("  2^50 - X   =",2**50-X)
print("  X as int50 =",X-(1<<50))
print("  真实 a0    =",x["a0"])
print("  真实 a1    =",x["a1"])
print("  a1/a0      = %.4f"%(x["a1"]/abs(x["a0"])))

print()
print("="*76); print("固定 slot3=2^200 全开收费，扫金额找完整分档"); print("="*76)
setslot(3,2**200)
seen={}
for e in range(0,25):
    v=10**e
    f=call(-v)
    seen.setdefault(f,[]).append(v)
    print("  amt=-1e%-3d fee=%d"%(e,f))
print()
print("费率档汇总:",{k:(min(v),max(v)) for k,v in seen.items()})
setslot(3,o3)
print("已还原 slot3 =",int(a.eth.get_storage_at(H3,3).hex(),16))
