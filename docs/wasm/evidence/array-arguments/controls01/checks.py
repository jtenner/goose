from pathlib import Path
import subprocess,json,sys,hashlib
r=Path('/home/dev/Projects/goose-wasm-backend');p=Path(__file__).parent;exe=p.parent/'build01/goose-tested';commands=[]
sys.path.insert(0,str(r/'test'))

def run(args,ok=True):
 args=list(map(str,args));name='command-'+str(len(commands));a=subprocess.run(args,cwd=r,capture_output=True,timeout=120)
 for ext,data in [('stdout',a.stdout),('stderr',a.stderr),('exit',(str(a.returncode)+'\n').encode())]:(p/(name+'.'+ext)).write_bytes(data)
 commands.append({'name':name,'args':args,'exit':a.returncode});(p/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
 if ok:assert not a.returncode,(name,args,a.stderr)
 return a
from wasm_array_argument_checks import check_images,check_aliases,check_guards
from wasm_aggregate_admission import check_admission
for opt in [0,2]:
 source=r/'test/wasm/wasm_array_argument_owner.goose';module=p/f'wasm_array_argument_owner-O{opt}.wasm';run([exe,f'-O{opt}','--target','wasm','-o',module,source])
 source=r/'test/wasm/wasm_array_argument_isolation.goose';module=p/f'wasm_array_argument_isolation-O{opt}.wasm';run([exe,f'-O{opt}','--target','wasm','-o',module,source])
counts={'images':check_images(run,'node','wasm-tools',p),'aliases':check_aliases(run,'node','wasm-tools',p),'guards':check_guards(run,exe,'cc',p),'admission':check_admission(run,exe,'cc',p,'node','wasm-tools',Path('/tmp/goose-wasm-runtime-env/bin/python'))}
(p/'counts.json').write_text(json.dumps(counts,indent=2)+'\n');print('PASS',counts)
