from pathlib import Path
import subprocess,sys,json
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');sys.path.insert(0,str(r/'test'))
from wasm_fixed_array_assignment_checks import check_failures
i=0
records=[]
def run(args,ok=True):
 global i
 i+=1;a=subprocess.run(list(map(str,args)),cwd=r,capture_output=True,timeout=120)
 for k,v in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (p/(f'command-{i:04}.'+k)).write_bytes(v)
 (p/f'command-{i:04}.json').write_text(json.dumps(list(map(str,args)))+'\n')
 if ok:assert not a.returncode,(args,a.stderr)
 return a
(p/'artifacts').mkdir(exist_ok=True)
n=check_failures(run,p.parent/'build01/goose-tested','cc','node','wasm-tools','/tmp/goose-wasm-runtime-env/bin/python',p/'artifacts')
assert n==8,n
(p/'results.json').write_text(json.dumps({'checks':n},indent=2)+'\n');print('PASS',n,'failure state and valid damaged controls')
