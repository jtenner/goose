from pathlib import Path
import sys,json,hashlib
class Reader:
 def __init__(self,data):self.data=data;self.pos=0
 def byte(self):v=self.data[self.pos];self.pos+=1;return v
 def u(self):
  value=shift=0
  while True:
   b=self.byte();value|=(b&127)<<shift
   if not b&128:return value
   shift+=7
 def take(self,n):v=self.data[self.pos:self.pos+n];self.pos+=n;assert len(v)==n;return v
 def name(self):return self.take(self.u()).decode()
def u(value):
 out=bytearray()
 while True:
  b=value&127;value>>=7;out.append(b|(128 if value else 0))
  if not value:return bytes(out)
def make_controls(module,out):
 data=module.read_bytes();assert data[:8]==b'\0asm\x01\0\0\0';r=Reader(data[8:]);sections=[];imports={};start=None
 while r.pos<len(r.data):
  ident=r.byte();body=r.take(r.u());sections.append((ident,body))
  if ident==2:
   a=Reader(body)
   for i in range(a.u()):
    namespace=a.name();name=a.name();assert a.byte()==0;a.u();imports[(namespace,name)]=i
  if ident==7:
   a=Reader(body)
   for _ in range(a.u()):
    name=a.name();kind=a.byte();index=a.u()
    if name=='_start':assert kind==0;start=index-len(imports)
 assert start is not None and start>=0
 additions={'print-owner':b'\x10'+u(imports[('goose','print_begin_v1')])+b'\x1a','snapshot-owner':b'\x41\0\x41\0\x41\0\x10'+u(imports[('goose','snapshot_memory_bytes_v1')])+b'\x1a'}
 out.mkdir();rows=[]
 for name,instructions in additions.items():
  result=bytearray(data[:8])
  for ident,body in sections:
   if ident==10:
    a=Reader(body);count=a.u();rebuilt=bytearray(u(count));assert start<count
    for i in range(count):
     function=a.take(a.u())
     if i==start:
      assert function[-1]==0x0b;function=function[:-1]+instructions+b'\x0b'
     rebuilt+=u(len(function))+function
    assert a.pos==len(body);body=bytes(rebuilt)
   result.append(ident);result+=u(len(body))+body
  target=out/(name+'.wasm');target.write_bytes(result);rows.append({'name':name,'sha256':hashlib.sha256(result).hexdigest(),'inserted_bytes':instructions.hex(),'target':'_start before its final end','intended_owner_count':1})
 (out/'controls.json').write_text(json.dumps({'healthy_sha256':hashlib.sha256(data).hexdigest(),'controls':rows},indent=2)+'\n')
if __name__=='__main__':make_controls(Path(sys.argv[1]),Path(sys.argv[2]))
