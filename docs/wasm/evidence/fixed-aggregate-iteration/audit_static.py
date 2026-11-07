"""Inspect saved Wasm bytes. This does not validate or execute modules."""
from pathlib import Path
import json
P=Path('/tmp/goose-wasm-aggregate-iteration-review-20261107');R=Path('/tmp/goose-wasm-aggregate-iteration-20261107/full-wasm01/artifacts')
class Reader:
 def __init__(self,data):self.d=data;self.p=0
 def byte(self):v=self.d[self.p];self.p+=1;return v
 def take(self,n):v=self.d[self.p:self.p+n];self.p+=n;return v
 def leb(self,signed=False):
  v=shift=0
  while True:
   b=self.byte();v|=(b&127)<<shift;shift+=7
   if not b&128:return v-(1<<shift) if signed and b&64 else v
 def name(self):return self.take(self.leb()).decode()
def inspect(path):
 r=Reader(path.read_bytes());assert r.take(8)==b'\0asm\x01\0\0\0';names={};bodies=[];imports=0
 while r.p<len(r.d):
  id=r.byte();s=Reader(r.take(r.leb()))
  if id==2:
   imports=s.leb()
   for _ in range(imports):s.name();s.name();assert s.byte()==0;s.leb()
  elif id==10:
   for _ in range(s.leb()):bodies.append(s.take(s.leb()))
  elif id==0 and s.name()=='name':
   while s.p<len(s.d):
    kind=s.byte();sub=Reader(s.take(s.leb()))
    if kind==1:
     for _ in range(sub.leb()):
      index=sub.leb();names[index]=sub.name()
 main=next(i for i,n in names.items() if n=='main.0');reserve=next(i for i,n in names.items() if n=='goose.reserve_frame')
 body=Reader(bodies[main-imports]);locals_=0
 for _ in range(body.leb()):locals_+=body.leb();body.byte()
 code_start=body.p;ins=[]
 while body.p<len(body.d):
  op=body.byte();args=[]
  if op in [2,3,4,0x41,0x42]:args=[body.leb(True)]
  elif op in [0x0c,0x0d,0x10,0x20,0x21,0x22,0x23,0x24,0x3f,0x40]:args=[body.leb()]
  elif 0x28<=op<=0x3e:
   flag=body.leb();args=[flag]
   if flag&64:args.append(body.leb())
   args.append(body.leb())
  elif op==0xfc:
   sub=body.leb();assert sub in [10,11];args=[sub,body.leb()]
   if sub==10:args.append(body.leb())
  elif op in [0x43,0x44]:args=[body.take(4 if op==0x43 else 8).hex()]
  else:assert op in [0,5,0x0b,0x0f,0x1a,0x1b] or 0x45<=op<=0xc4,hex(op)
  ins.append((op,args))
 loop=next(i for i,(op,_) in enumerate(ins) if op==3)
 calls=[i for i,x in enumerate(ins) if x==(0x10,[reserve])]
 copies=[i for i,(op,args) in enumerate(ins) if op==0xfc and args[0]==10]
 assert len(calls)==1 and calls[0]<loop and ins[calls[0]-1]==(0x41,[8])
 assert len(copies)==1 and copies[0]>loop and ins[copies[0]]==(0xfc,[10,0,0])
 return {'file':path.name,'module_bytes':path.stat().st_size,'main_body_bytes':len(body.d),'main_instruction_bytes':len(body.d)-code_start,'main_locals':locals_,'binder_frame_bytes':8,'loop_copy_sites':1,'reserve_before_loop':True,'copy_memories':[0,0]}
rows=[]
for saved in json.loads((R/'iteration-footprint.json').read_text()):
 file=R/f"iteration-{saved['kind']}-{saved['value']}-O{saved['opt']}.wasm";row=inspect(file)
 assert row['module_bytes']==saved['bytes'] and row['main_locals']==saved['main_locals']
 rows.append(row)
(P/'review/static-audit.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
