"""Temporary designated receiver. Receipts contain synthetic bytes only."""
import socket,threading,http.server,json,time,base64,sys,struct,hashlib
CONFIG=json.load(open(sys.argv[1]));CANARY=bytes.fromhex(CONFIG['canary_hex']);OUT=CONFIG['receipt_path'];LOCK=threading.Lock()
def record(protocol,data,peer,tag=None):
 recovered=data
 if protocol=='dns-format':
  try:
   off=12;labels=[]
   while data[off]:
    size=data[off];labels.append(data[off+1:off+1+size]);off+=size+1
   if data[off:off+5]!=b'\x00\x00\x10\x00\x01' or len(labels)!=5 or labels[-1]!=b'lab':raise ValueError('DNS envelope')
   tag=labels[0].decode('ascii');recovered=bytes.fromhex(b''.join(labels[1:4]).decode('ascii'))
  except Exception:recovered=b''
 current=json.load(open(sys.argv[1]))
 if recovered.hex()!=current['canary_hex']:return False
 r={'received_at':time.time(),'protocol':protocol,'tag':tag,'peer':peer,'wire_bytes':len(data),'payload_bytes':len(recovered),'payload_hex':recovered.hex(),'sha256':hashlib.sha256(recovered).hexdigest()}
 with LOCK:
  with open(OUT,'a') as f:f.write(json.dumps(r)+'\n')
 return True
class Admin(http.server.BaseHTTPRequestHandler):
 def do_GET(self):
  if self.path!='/receipts':self.send_error(404);return
  self.send_response(200);self.end_headers()
  with LOCK:
   try:self.wfile.write(open(OUT,'rb').read())
   except FileNotFoundError:pass
 def do_POST(self):
  if self.path!='/fixture':self.send_error(404);return
  size=int(self.headers.get('Content-Length','0'))
  if size!=128:self.send_error(400);return
  try:
   hx=self.rfile.read(size).decode('ascii');assert len(bytes.fromhex(hx))==64
   current=json.load(open(sys.argv[1]));current['canary_hex']=hx
   with open(sys.argv[1]+'.next','w') as f:json.dump(current,f)
   import os;os.replace(sys.argv[1]+'.next',sys.argv[1])
  except Exception:self.send_error(400);return
  self.send_response(200);self.end_headers();self.wfile.write(b'OK')
 def log_message(self,*a):pass
threading.Thread(target=lambda:http.server.ThreadingHTTPServer(('0.0.0.0',19084),Admin).serve_forever(),daemon=True).start()
class HTTP(http.server.BaseHTTPRequestHandler):
 def do_POST(self):
  size=int(self.headers.get('Content-Length','0'))
  if size!=64:self.send_error(400);return
  data=self.rfile.read(size);ok=record('http',data,self.client_address,self.path.lstrip('/'))
  self.send_response(200 if ok else 400);self.end_headers();self.wfile.write(b'ACK' if ok else b'REJECT')
 def log_message(self,*args):pass
def tcp(port):
 s=socket.socket();s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);s.bind(('0.0.0.0',port));s.listen()
 while True:
  c,p=s.accept();c.settimeout(4)
  try:
   data=b''
   while len(data)<64:
    x=c.recv(64-len(data))
    if not x:break
    data+=x
   ok=record('tcp',data,p);c.sendall(b'ACK' if ok else b'REJECT')
  except Exception:pass
  finally:c.close()
def udp(port,protocol):
 s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);s.bind(('0.0.0.0',port))
 while True:
  data,p=s.recvfrom(2048);ok=record(protocol,data,p)
  if ok:s.sendto(b'ACK',p)
for fn,args in [(tcp,(CONFIG['ports']['tcp'],)),(udp,(CONFIG['ports']['udp'],'udp')),(udp,(CONFIG['ports']['dns'],'dns-format'))]:threading.Thread(target=fn,args=args,daemon=True).start()
print('receiver ready',flush=True)
http.server.ThreadingHTTPServer(('0.0.0.0',CONFIG['ports']['http']),HTTP).serve_forever()
