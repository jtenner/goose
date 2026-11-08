from pathlib import Path
import subprocess,sys,json
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');sys.path.insert(0,str(r/'test'))
from wasm_fixed_binary_checks import check_images,check_snapshot,check_loop,check_failures
import hashlib
i=0
records=[]
reused=[]
for n,h in json.loads((p/'reused-artifact-hashes.json').read_text()).items():
 assert hashlib.sha256((p/'artifacts'/n).read_bytes()).hexdigest()==h,n
def run(args,ok=True):
 global i
 args=list(map(str,args))
 old=p.parent/'image02'
 for record in sorted(old.glob('command-*.json')):
  saved=json.loads(record.read_text())
  normalized=[x.replace(str(p),str(old)) for x in args]
  if saved==normalized:
   stem=str(record.with_suffix(''))
   reused.append({'command':str(record),'sha256':hashlib.sha256(record.read_bytes()).hexdigest()})
   (p/'reused-commands.json').write_text(json.dumps(reused,indent=2)+'\n')
   return subprocess.CompletedProcess(args,int(Path(stem+'.exit').read_text()),Path(stem+'.stdout').read_bytes(),Path(stem+'.stderr').read_bytes())
 i+=1;a=subprocess.run(list(map(str,args)),cwd=r,capture_output=True,timeout=120)
 for k,v in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (p/(f'command-{i:04}.'+k)).write_bytes(v)
 (p/f'command-{i:04}.json').write_text(json.dumps(list(map(str,args)))+'\n')
 if ok:assert not a.returncode,(args,a.stderr)
 return a
n=check_failures(run,p.parent/'build01/goose-tested','cc','node','wasm-tools',p/'artifacts')
assert n==6
(p/'results.json').write_text(json.dumps({'failures':n},indent=2)+'\n');print('PASS failures',n,flush=True)
