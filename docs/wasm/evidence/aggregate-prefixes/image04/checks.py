from pathlib import Path
import subprocess,sys,json
r=Path('/home/dev/Projects/goose-wasm-backend');p=Path(__file__).parent;sys.path.insert(0,str(r/'test'))
from wasm_aggregate_prefix_checks import check_images,check_dynamic,check_guards
i=0
def run(args,ok=True):
 global i
 i+=1;args=list(map(str,args));a=subprocess.run(args,cwd=r,capture_output=True,timeout=120)
 (p/f'command-{i:04}.json').write_text(json.dumps(args)+'\n')
 for k,v in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (p/f'command-{i:04}.{k}').write_bytes(v)
 assert not ok or not a.returncode,(args,a.returncode,a.stderr)
 return a
n=check_images(run,'node','wasm-tools',p.parent/'focused03')
n+=check_dynamic(run,'node','wasm-tools',p.parent/'focused04')
n+=check_guards(run,p.parent/'build02/goose-tested','cc',p)
print('PASS',n,'image/identity/cleanup/guard checks')
