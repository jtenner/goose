from pathlib import Path
import subprocess,sys,json
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');sys.path.insert(0,str(r/'test'))
from wasm_negation_adaptation_checks import check_images,check_prefixes,check_loop
i=0
records=[]
def run(args,ok=True):
 global i
 i+=1;a=subprocess.run(list(map(str,args)),cwd=r,capture_output=True,timeout=120)
 for k,v in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (p/(f'command-{i:04}.'+k)).write_bytes(v)
 (p/f'command-{i:04}.json').write_text(json.dumps(list(map(str,args)))+'\n')
 if ok:assert not a.returncode,(args,a.stderr)
 return a
for name,check in [('images',check_images),('prefixes',check_prefixes),('loop',check_loop)]:
 n=check(run,'node','wasm-tools',p/'artifacts');records.append({'name':name,'checks':n});(p/'results.json').write_text(json.dumps(records,indent=2)+'\n');print('PASS',name,n,flush=True)
assert [x['checks'] for x in records]==[26,16,4],records
