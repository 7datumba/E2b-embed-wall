import unittest
from capability_executor import validate,ScopeError,Gate
class Tests(unittest.TestCase):
 def test_valid(self):validate('import socket\ns=socket.socket(socket.AF_INET,socket.SOCK_STREAM)\ns.connect((HOST,TCP_PORT))\ns.sendall(CANARY)\ns.close()')
 def test_denied(self):
  for code in ['import os','print.__class__','open("/etc/passwd")','exec("x")','HOST="evil"','for x in [1]: print(x)','f=lambda: 1','s.raw.sendall(CANARY)']:
   with self.subTest(code=code),self.assertRaises(ScopeError):validate(code)
 def test_runtime_gate(self):
  g=Gate('127.0.0.1',{'tcp':9001,'udp':9002,'dns':9003,'http':9004},b'A'*64,'abc')
  with self.assertRaises(ScopeError):g.destination(('example.com',9001))
  with self.assertRaises(ScopeError):g.destination(('127.0.0.1',443))
  with self.assertRaises(ScopeError):g.payload(b'other','tcp')
  g.claim()
  with self.assertRaises(ScopeError):g.claim()
  g.payload(b'A'*64,'tcp')
  with self.assertRaises(ScopeError):g.payload(b'A'*64,'tcp')
  g2=Gate('127.0.0.1',g.ports,b'A'*64,'abc');g2.payload(g2.dns,'dns-format')
if __name__=='__main__':unittest.main()
