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
SENDER=Web3.to_checksum_address(x["sender"])
def cd(amt,z=True):
    return "0x"+(SEL+encode(["address","(address,address,uint24,int24,address)","(bool,int256,uint160)","bytes"],
        [SENDER,(C0,C1,0x800000,60,H3),(z,amt,MIN),b""])).hex()
def hx(n): return "0x"+("%064x"%n)
def setslot(slot,val):
    r=a.provider.make_request("anvil_setStorageAt",[H3,hx(slot),hx(val)])
    return "error" not in r
def call(amt):
    r=a.provider.make_request("eth_call",[{"from":PM,"to":H3,"data":cd(amt)},"latest"])
    if "error" in r: return None,str(r["error"])[:50]
    raw=bytes.fromhex(r["result"][2:])
    v=int.from_bytes(raw[36:68],"big")
    return v&0xffffff, v

amt=-abs(x["a0"])
print("基线 slot3=5000000:", call(amt))
print()
print("="*76)
print("anvil_setStorageAt 改 slot3")
print("="*76)
orig=int(a.eth.get_storage_at(H3,3).hex(),16)
print("原值:",orig)
for thr in [1000000,100000,1000,1,0]:
    ok=setslot(3,thr)
    f,raw=call(amt)
    print("  slot3=%-10d setOK=%-5s fee=%-8s raw=0x%x"%(thr,ok,f,raw if isinstance(raw,int) else 0))
setslot(3,orig)
print("已还原 slot3 =",int(a.eth.get_storage_at(H3,3).hex(),16))
