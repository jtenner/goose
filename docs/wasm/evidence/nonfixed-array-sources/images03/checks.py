from pathlib import Path
import subprocess,sys,json
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');sys.path.insert(0,str(r/'test'))
from wasm_nonfixed_source_checks import check_failures
i=0
def run(args,ok=True):
 global i
 i+=1;args=list(map(str,args));a=subprocess.run(args,cwd=r,capture_output=True,timeout=120)
 (p/f'command-{i:04}.json').write_text(json.dumps(args)+'\n')
 for k,v in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (p/f'command-{i:04}.{k}').write_bytes(v)
 assert not ok or not a.returncode,(args,a.returncode,a.stderr)
 return a
n=check_failures(run,p.parent/'build01/goose-tested','cc','node','wasm-tools','/tmp/goose-wasm-runtime-env/bin/python',p/'artifacts');print('PASS',n,'specific range/product/sum guard checks')
