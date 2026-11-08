from pathlib import Path
import subprocess,json,sys,hashlib
r=Path('/home/dev/Projects/goose-wasm-backend');p=Path(__file__).parent;exe=p.parent/'build03/goose-tested';commands=[]
sys.path.insert(0,str(r/'test'))

def run(args,ok=True):
 args=list(map(str,args));name='command-'+str(len(commands));a=subprocess.run(args,cwd=r,capture_output=True,timeout=120)
 for ext,data in [('stdout',a.stdout),('stderr',a.stderr),('exit',(str(a.returncode)+'\n').encode())]:(p/(name+'.'+ext)).write_bytes(data)
 commands.append({'name':name,'args':args,'exit':a.returncode});(p/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
 if ok:assert not a.returncode,(name,args,a.stderr)
 return a
rows=[]
for source in sorted((r/'test/wasm').glob('*.goose')):
 for opt in [0,2]:
  module=p/(source.stem+f'-O{opt}.wasm');run([exe,f'-O{opt}','--target','wasm','-o',module,source]);original=p.parent/'full-correctness01/artifacts'/module.name
  assert module.read_bytes()==original.read_bytes(),(source,opt)
  rows.append({'source':str(source.relative_to(r)),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'opt':opt,'module_sha256':hashlib.sha256(module.read_bytes()).hexdigest(),'status':'identical'})
(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n');assert len(rows)==528;print('PASS',len(rows),'fixture modules identical after indexed-owner refinement')
from wasm_fixed_argument_checks import check_images,check_aliases,check_guards,check_dynamic
counts={'images':check_images(run,'node','wasm-tools',p),'aliases':check_aliases(run,'node','wasm-tools',p),'guards':check_guards(run,exe,'cc',p),'dynamic':check_dynamic(run,'node','wasm-tools',p)}
(p/'counts.json').write_text(json.dumps(counts,indent=2)+'\n');print('PASS',counts)
