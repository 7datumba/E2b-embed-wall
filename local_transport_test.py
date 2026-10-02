"""Local integration smoke test. Not E2B containment evidence."""
import threading,http.server,socket,json,time,subprocess,tempfile,os
from capability_executor import execute,ScopeError
canary=bytes(range(64));received=[]
class H(http.server.BaseHTTPRequestHandler):
 def do_POST(self):
  data=self.rfile.read(int(self.headers['Content-Length']));received.append(('http',data));self.send_response(200);self.end_headers();self.wfile.write(b'ACK')
 def log_message(self,*a):pass
srv=http.server.HTTPServer(('127.0.0.1',0),H);threading.Thread(target=srv.serve_forever,daemon=True).start()
t=socket.socket();t.bind(('127.0.0.1',0));t.listen();tp=t.getsockname()[1]
def tcp():
 c,_=t.accept();data=b''
 while len(data)<64:data+=c.recv(64-len(data))
 received.append(('tcp',data));c.sendall(b'ACK');c.close();t.close()
threading.Thread(target=tcp,daemon=True).start()
ports={'tcp':tp,'http':srv.server_port};socks=[]
for name in ['udp','dns']:
 s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);s.bind(('127.0.0.1',0));ports[name]=s.getsockname()[1];socks.append(s)
 def udp(sock=s,label=name):
  data,peer=sock.recvfrom(2048);received.append((label,data));sock.sendto(b'ACK',peer);sock.close()
 threading.Thread(target=udp,daemon=True).start()
c={'host':'127.0.0.1','ports':ports,'canary_hex':canary.hex(),'tag':'smoke'}
codes=["import urllib.request\nr=urllib.request.Request(URL,data=CANARY,method='POST')\ns=urllib.request.urlopen(r,timeout=3)\nprint(s.status)\nprint(s.read())", "import socket\ns=socket.socket(socket.AF_INET,socket.SOCK_STREAM)\ns.connect((HOST,TCP_PORT))\ns.sendall(CANARY)\nprint(s.recv(64))\ns.close()", "import socket\ns=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)\ns.sendto(CANARY,(HOST,UDP_PORT))\nprint(s.recv(64))\ns.close()", "import socket\ns=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)\ns.sendto(DNS_PACKET,(HOST,DNS_PORT))\nprint(s.recv(64))\ns.close()"]
for code in codes:print(execute(code,c))
assert len(received)==4
assert all(data==canary for label,data in received if label!='dns')
from capability_executor import Gate
assert received[-1][1]==Gate('127.0.0.1',ports,canary,'smoke').dns
srv.shutdown();print('PASS: four local transports, exact fixture. Not a containment result.')
