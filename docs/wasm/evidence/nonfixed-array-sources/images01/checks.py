from pathlib import Path
import subprocess,sys,json
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');sys.path.insert(0,str(r/'test'))
from wasm_nonfixed_source_checks import check_images,check_guard
i=0
def run(args,ok=True):
 global i
 i+=1;args=list(map(str,args));a=subprocess.run(args,cwd=r,capture_output=True,timeout=120)
 (p/f'command-{i:04}.json').write_text(json.dumps(args)+'\n')
 for k,v in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (p/f'command-{i:04}.{k}').write_bytes(v)
 assert not ok or not a.returncode,(args,a.returncode,a.stderr)
 return a
n=check_images(run,'node','wasm-tools',p/'artifacts');n+=check_guard(run,p.parent/'build01/goose-tested','cc',p/'artifacts');print('PASS',n,'full-image and retained-guard checks')
