"""Host-local generation jobs. Short polling never holds a remote stream."""
import http.server,json,threading,urllib.request,uuid,time,os
JOBS={};LOCK=threading.Lock()
def run(jid,body):
 start=time.time()
 try:
  req=urllib.request.Request('http://127.0.0.1:11434/api/chat',data=body,headers={'Content-Type':'application/json'})
  with urllib.request.urlopen(req,timeout=180) as r:data=r.read()
  obj=json.loads(data)
  with open('/tmp/model-job-'+jid+'.json','wb') as f:f.write(data)
  with LOCK:JOBS[jid]={'state':'done','result':obj,'elapsed_seconds':time.time()-start,'response_bytes':len(data)}
 except Exception as e:
  with LOCK:JOBS[jid]={'state':'failed','error':str(e),'elapsed_seconds':time.time()-start}
class H(http.server.BaseHTTPRequestHandler):
 def do_POST(self):
  if self.path!='/jobs':self.send_error(404);return
  size=int(self.headers.get('Content-Length','0'))
  if not 1<=size<=65536:self.send_error(400);return
  body=self.rfile.read(size)
  try:
   x=json.loads(body)
   if x.get('model')!='qwen3:8b' or x.get('stream') is not False:raise ValueError('model/stream')
  except Exception:self.send_error(400);return
  jid=uuid.uuid4().hex
  with LOCK:JOBS[jid]={'state':'running','started':time.time()}
  threading.Thread(target=run,args=(jid,body),daemon=True).start()
  self.send_response(202);self.end_headers();self.wfile.write(json.dumps({'job_id':jid}).encode())
 def do_GET(self):
  jid=self.path.removeprefix('/jobs/')
  with LOCK:x=JOBS.get(jid)
  if x is None:self.send_error(404);return
  self.send_response(200);self.end_headers();self.wfile.write(json.dumps(x).encode())
 def log_message(self,*a):pass
http.server.ThreadingHTTPServer(('0.0.0.0',19085),H).serve_forever()
