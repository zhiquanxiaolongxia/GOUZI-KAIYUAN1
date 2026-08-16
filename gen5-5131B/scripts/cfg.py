from web3 import Web3
w3=Web3(Web3.HTTPProvider("https://robinhood.rpc.blxrbdn.com",request_kwargs={"timeout":120}))
G3=Web3.to_checksum_address("0x31Ac5B793C073C7EB15CfC259963CD60004f4080")
G5=Web3.to_checksum_address("0x42554Fa546995A393D19B3880D3a4C6709298080")

def dump(h,name):
    print("="*76); print("%s  %s"%(name,h)); print("="*76)
    s=[int(w3.eth.get_storage_at(h,i).hex(),16) for i in range(5)]
    for i,v in enumerate(s): print("  slot%-2d = 0x%064x"%(i,v))
    print()
    b1=s[1].to_bytes(32,"big")
    # slot1 高位起: [pad][t3][t2][t1][dynflag]
    t3=int.from_bytes(b1[3:6],"big"); t2=int.from_bytes(b1[6:9],"big")
    t1=int.from_bytes(b1[9:12],"big"); dyn=int.from_bytes(b1[11:14],"big")
    print("  slot1 拆解:")
    print("     tier3(最高档) = %-8d = %.3f%%"%(t3,t3/10000))
    print("     tier2         = %-8d = %.3f%%"%(t2,t2/10000))
    print("     tier1(最低档) = %-8d = %.3f%%"%(t1,t1/10000))
    print("     dynFlag       = 0x%x"%dyn)
    b2=s[2].to_bytes(32,"big")
    th1=int.from_bytes(b2[26:29],"big"); th2=int.from_bytes(b2[29:32],"big")
    print("  slot2 拆解:")
    print("     thrA = %d"%int.from_bytes(b2[23:26],"big"))
    print("     thrB = %d"%th1)
    print("     thrC = %d"%th2)
    print("  slot3 = %d  (LT 比较阈值)"%s[3])
    print("  slot0 owner = 0x%040x"%(s[0]&((1<<160)-1)))
    print()
    return s

s3=dump(G3,"三代 USDG/FRONG")
s5=dump(G5,"五代 ETH/xxx")

print("="*76); print("两代对比"); print("="*76)
print("%-14s %-26s %-26s"%("slot","三代","五代"))
for i in range(5):
    print("%-14s 0x%-24x 0x%-24x %s"%("slot%d"%i,s3[i],s5[i],"  <-- 相同" if s3[i]==s5[i] else ""))
