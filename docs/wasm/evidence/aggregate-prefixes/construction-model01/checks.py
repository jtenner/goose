from pathlib import Path
import subprocess,json,sys
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');sys.path.insert(0,str(r/'test'))
from wasm_aggregate_construction_checks import check_modules
i=0
def run(args,ok=True):
 global i
 i+=1;args=list(map(str,args));a=subprocess.run(args,cwd=r,capture_output=True,timeout=120)
 (p/f'command-{i:03}.json').write_text(json.dumps(args)+'\n')
 for k,v in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (p/f'command-{i:03}.{k}').write_bytes(v)
 assert not ok or not a.returncode,(args,a.returncode,a.stderr)
 return a
n=check_modules(run,'node','wasm-tools',p/'artifacts');print('PASS',n,'complete construction image/ownership checks and specific controls')
