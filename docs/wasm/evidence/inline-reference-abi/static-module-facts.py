from pathlib import Path
import json
root=Path(__file__).parent
old=Path('/tmp/goose-wasm-array-places-20261107/build02');new=root/'full-wasm01/artifacts'
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
def facts(path):
 data=path.read_bytes();assert data[:8]==b'\0asm\x01\0\0\0';r=Reader(data[8:]);sections={};names={}
 while r.pos<len(r.data):
  ident=r.byte();body=r.take(r.u())
  if ident:sections[ident]=body
  else:
   custom=Reader(body)
   if custom.name()=='name':
    while custom.pos<len(custom.data):
     kind=custom.byte();sub=Reader(custom.take(custom.u()))
     if kind==1:
      for _ in range(sub.u()):
       index=sub.u();names[index]=sub.name()
 t=Reader(sections[1]);types=[]
 for _ in range(t.u()):
  assert t.byte()==0x60
  params=list(t.take(t.u()));results=list(t.take(t.u()));types.append((params,results))
 imported=0
 if 2 in sections:
  t=Reader(sections[2])
  for _ in range(t.u()):
   t.name();t.name();assert t.byte()==0;t.u();imported+=1
 t=Reader(sections[3]);indices=[t.u() for _ in range(t.u())]
 t=Reader(sections[10]);functions=[];labels={0x7f:'i32',0x7e:'i64',0x7d:'f32',0x7c:'f64'}
 for i in range(t.u()):
  b=Reader(t.take(t.u()));locals={}
  for _ in range(b.u()):
   count=b.u();kind=labels[b.byte()];locals[kind]=locals.get(kind,0)+count
  params,results=types[indices[i]]
  functions.append({'name':names[imported+i],'params':[labels[v] for v in params],'results':[labels[v] for v in results],'locals':locals,'local_slots':sum(locals.values()),'instruction_bytes':len(b.data)-b.pos})
 return {'module_bytes':len(data),'type_count':len(types),'function_count':len(functions),'code_section_bytes':len(sections[10]),'local_slots':sum(f['local_slots'] for f in functions),'helper_names':[f['name'] for f in functions if f['name'].startswith('goose.')],'functions':functions}
rows=[]
for entry in json.loads((root/'compatibility01/prior-module-deltas.json').read_text()):
 if entry['identical']:continue
 stem=Path(entry['source']).stem+'-O'+str(entry['opt']);a=facts(old/(stem+'-after.wasm'));b=facts(new/(stem+'.wasm'))
 before={f['name']:f for f in a['functions']};after={f['name']:f for f in b['functions']}
 assert len(before)==a['function_count'] and len(after)==b['function_count']
 row={'source':entry['source'],'opt':entry['opt'],'module_bytes_delta':b['module_bytes']-a['module_bytes'],'code_section_bytes_delta':b['code_section_bytes']-a['code_section_bytes'],'type_count_delta':b['type_count']-a['type_count'],'function_count_delta':b['function_count']-a['function_count'],'local_slots_delta':b['local_slots']-a['local_slots'],'helpers_added':sorted(set(b['helper_names'])-set(a['helper_names'])),'helpers_removed':sorted(set(a['helper_names'])-set(b['helper_names'])),'changed_function_metadata':[{'name':n,'parent':before.get(n),'candidate':after.get(n)} for n in sorted(set(before)|set(after)) if before.get(n)!=after.get(n)]}
 rows.append(row)
(root/'module-structure-deltas.json').write_text(json.dumps(rows,indent=2)+'\n')
print(str(len(rows))+' changed module pairs have static type/local/helper/code metadata; no module was executed.')
