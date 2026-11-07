from pathlib import Path
import hashlib,json,sys
r=Path('/home/dev/Projects/goose-wasm-backend');p=Path(__file__).parent
sys.path.insert(0,str(r/'test'))
from wasm_backend import function_local_counts

def metrics(data):
 def leb(pos):
  value=shift=0
  while True:
   x=data[pos];pos+=1;value|=(x&127)<<shift
   if not x&128:return value,pos
   shift+=7
 pos=8;code=0
 while pos<len(data):
  tag=data[pos];size,start=leb(pos+1)
  if tag==10:code+=size
  pos=start+size
 assert pos==len(data)
 locals_=function_local_counts(data)
 return {'module_bytes':len(data),'code_section_bytes':code,'functions':len(locals_),'local_count':sum(locals_),'max_function_locals':max(locals_,default=0)}
rows=[]
for e in json.loads((p/'module-deltas.json').read_text()):
 values=[]
 for name,key in [('parent','parent_module'),('candidate','candidate_module')]:
  data=Path(e[key]).read_bytes();assert hashlib.sha256(data).hexdigest()==e[name+'_sha256'];values.append(metrics(data))
 rows.append({'source':e['source'],'opt':e['opt'],'parent':values[0],'candidate':values[1], 'delta':{k:values[1][k]-values[0][k] for k in values[0]}})
summary={'pairs':len(rows),'total_deltas':{k:sum(x['delta'][k] for x in rows) for k in rows[0]['delta']},'limit':'Saved Wasm artifacts only. No compiler/guest execution, CPU, allocation, RSS or physical memory result.'}
(p/'module-metadata.json').write_text(json.dumps({'summary':summary,'rows':rows},indent=2)+'\n');print(json.dumps(summary))
