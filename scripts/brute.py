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
PID=bytes.fromhex("bd317ebfd767c06e3723fa1bccf48a6ac6931bf4c94a23a0669e21472b714d47")
def hx(n): return "0x"+("%064x"%n)
def setraw(slot_hex,val_hex):
    a.provider.make_request("anvil_setStorageAt",[H3,slot_hex,val_hex])
def call(amt=None):
    if amt is None: amt=-abs(x["a0"])
    d=SEL+encode(["address","(address,address,uint24,int24,address)","(bool,int256,uint160)","bytes"],
     [Web3.to_checksum_address(x["sender"]),(C0,C1,0x800000,60,H3),(True,amt,MIN),b""])
    r=a.eth.call({"from":PM,"to":H3,"data":d})
    w=int.from_bytes(r[64:96],"big")
    return w&0x3FFFFF, bool(w&(1<<22))

print("基线 fee=%d"%call()[0])
print()
print("="*76)
print("暴力搜索：逐个改裸槽 0..12，看哪个让 fee 变非零")
print("="*76)
base={}
for s in range(13):
    base[s]=a.eth.get_storage_at(H3,s).hex()
for s in range(13):
    orig=base[s]
    for probe in [hx(0), hx(1), hx(2**200), "0x"+"ff"*32]:
        setraw(hx(s),probe)
        try:
            f,ov=call()
        except Exception as e:
            f,ov=("EXC",str(e)[:30])
        if f not in (0,"EXC"):
            print("  slot%-3d probe=%s...  -> fee=%s override=%s  <<<"%(s,probe[:18],f,ov))
    setraw(hx(s),"0x"+orig if not orig.startswith("0x") else orig)

print()
print("="*76)
print("改 mapping keccak(poolId,4) 计数器值")
print("="*76)
cslot=hx(int(a.keccak(PID+(4).to_bytes(32,"big")).hex(),16))
corig=a.eth.get_storage_at(H3,int(cslot,16)).hex()
for v in [0,1,2,3,5,10,100,1000,10**6]:
    setraw(cslot,hx(v))
    f,ov=call()
    print("  counter=%-10d fee=%-8d %s"%(v,f,"<<<" if f>0 else ""))
setraw(cslot,"0x"+corig if not corig.startswith("0x") else corig)
