import sys,json,os
path='/tmp/receiver-config.json'
x=json.load(open(path));canary=bytes.fromhex(sys.argv[1])
if len(canary)!=64:raise ValueError('64-byte fixture only')
x['canary_hex']=canary.hex()
with open(path+'.next','w') as f:json.dump(x,f)
os.replace(path+'.next',path)
