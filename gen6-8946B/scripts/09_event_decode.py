from web3 import Web3
import pickle, collections, time
URL="https://robinhood.rpc.blxrbdn.com"
def mk(): return Web3(Web3.HTTPProvider(URL,request_kwargs={"timeout":60}))
w3=mk()
def rpc(fn):
    global w3
    for a in range(6):
        try: return fn()
        except Exception as e:
            if a==5: raise
            time.sleep(2*(a+1)); w3=mk()
evts=pickle.load(open("/tmp/h8evt.pkl","rb"))
print("事件数",len(evts))
print("="*88); print("S-12: hook 事件全解（topic + data）"); print("="*88)
bytopic=collections.defaultdict(list)
for bn,li,ad,tps,data in evts: bytopic[tps[0]].append((bn,li,ad,tps,data))
for t,rows in sorted(bytopic.items(),key=lambda x:-len(x[1])):
    print("\n  topic %s   count=%d"%(t,len(rows)))
    for bn,li,ad,tps,data in rows[:6]:
        d=data[2:] if data.startswith("0x") else data
        words=[d[i:i+64] for i in range(0,len(d),64)]
        print("    blk=%d %s topics=%d"%(bn,ad[:10],len(tps)))
        for j,tp in enumerate(tps[1:],1): print("       t%d = %s"%(j,tp))
        for j,wd in enumerate(words):
            iv=int(wd,16)
            print("       d%d = %s  (%d)"%(j,wd,iv))
print()
print("="*88); print("S-13: 两个池的元信息 (Initialize)"); print("="*88)
POOLS=["0xa53aed8eb6f4c8a2c5d990c261868f45d2b2f10b13f1b14924ef5a6e614f2a28",
       "0x717fd7ee0f0725ea031dc19e60b040b5dd21fdcc94cb3e871bf0e27b020effa1"]
PM=Web3.to_checksum_address("0x8366a39CC670B4001A1121B8F6A443A643e40951")
INIT="0x"+w3.keccak(text="Initialize(bytes32,address,address,uint24,int24,address,uint160,int24)").hex().lstrip("0x")
print(" Initialize topic:",INIT)
tip=rpc(lambda: w3.eth.block_number)
import concurrent.futures as cf
def pull(r):
    a,b=r
    try: return rpc(lambda: w3.eth.get_logs({"fromBlock":a,"toBlock":b,"address":PM,"topics":[INIT]}))
    except Exception: return []
STEP=500000
rngs=[(s,min(s+STEP-1,tip)) for s in range(tip-8000000,tip+1,STEP)]
inits=[]
with cf.ThreadPoolExecutor(5) as ex:
    for r in ex.map(pull,rngs): inits.extend(r)
print("  Initialize 事件总数:",len(inits))
for lg in inits:
    pid="0x"+lg["topics"][1].hex().lstrip("0x")
    pid_n=lg["topics"][1].hex()
    if any(p.lstrip("0x") in pid_n for p in POOLS):
        d=lg["data"].hex(); d=d[2:] if d.startswith("0x") else d
        w=[d[i:i+64] for i in range(0,len(d),64)]
        print("\n  ★ poolId %s  blk=%d"%(pid_n,lg["blockNumber"]))
        print("     c0=0x%s"%lg["topics"][2].hex()[-40:])
        print("     c1=0x%s"%lg["topics"][3].hex()[-40:])
        for j,x in enumerate(w): print("     d%d=%s (%d)"%(j,x,int(x,16)))
