from pathlib import Path
import json,subprocess,hashlib
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');exe=p.parent/'build01/goose-tested';rows=[]
def run(name,args):
 a=subprocess.run(list(map(str,args)),cwd=r,capture_output=True,timeout=120)
 for k,v in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (p/(name+'.'+k)).write_bytes(v)
 return a
for name,src in json.loads((p.parent/'matrix-cases.json').read_text()).items():
 f=p/(name+'.goose');f.write_text(src);c=p/(name+'.c');out=p/(name+'.native')
 a=run(name+'-emit',[exe,'-O0','--standalone','-o',c,f]);row={'name':name,'emit_exit':a.returncode,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
 if not a.returncode:
  a=run(name+'-cc',['cc',c,'-pthread','-lm','-ldl','-o',out]);row['cc_exit']=a.returncode
  if not a.returncode:
   a=run(name+'-run',[out]);row.update(exit=a.returncode,stdout=a.stdout.decode(),stderr=a.stderr.decode())
 rows.append(row)
assert len(rows)==44 and all(x.get('emit_exit')==0 and x.get('cc_exit')==0 and x.get('exit')==0 and x.get('stdout')==x['name']+'\n' for x in rows),rows
(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
