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

def cd(amt,z=True,sender=SENDER):
    return "0x"+(SEL+encode(["address","(address,address,uint24,int24,address)","(bool,int256,uint160)","bytes"],
        [sender,(C0,C1,0x800000,60,H3),(z,amt,MIN),b""])).hex()

def slot_hex(n): return "0x"+("%064x"%n)

print("="*76)
print("stateOverride: 把 slot3 从 5,000,000 改成各种值，翻转 LT 分支")
print("="*76)
amt=-abs(x["a0"])
for thr in [5000000, 1000000, 100000, 1000, 1, 0]:
    ov={H3:{"stateDiff":{slot_hex(3):slot_hex(thr)}}}
    try:
        r=a.provider.make_request("eth_call",[{"from":PM,"to":H3,"data":cd(amt)},"latest",ov])
        if "error" in r:
            print("  slot3=%-10d ERR %s"%(thr,str(r["error"])[:60])); continue
        raw=bytes.fromhex(r["result"][2:])
        fee=int.from_bytes(raw[36:68],"big")&0xffffff
        flag=int.from_bytes(raw[36:68],"big")
        print("  slot3=%-10d -> fee=%-8d raw=0x%x"%(thr,fee,flag))
    except Exception as e:
        print("  slot3=%-10d EXC %s"%(thr,str(e)[:60]))
