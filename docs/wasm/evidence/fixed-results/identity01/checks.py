from pathlib import Path
import subprocess,json,hashlib
r=Path('/home/dev/Projects/goose-wasm-backend');p=Path(__file__).parent;exe=p.parent/'build02/goose-tested';rows=[]
roots=[Path('/tmp/goose-wasm-fixed-arguments-20261107/identity03'),Path('/tmp/goose-wasm-fixed-arguments-20261107/scalar04')]
for root in roots:
 for original in sorted(root.glob('wasm_*.wasm')):
  source=r/'test/wasm'/(original.stem.rsplit('-O',1)[0]+'.goose');opt=original.stem.rsplit('-O',1)[1]
  module=p/original.name;a=subprocess.run([str(exe),'-O'+opt,'--target','wasm','-o',str(module),str(source)],cwd=r,capture_output=True)
  for ext,data in [('stdout',a.stdout),('stderr',a.stderr),('exit',(str(a.returncode)+'\n').encode())]:(p/(module.stem+'.'+ext)).write_bytes(data)
  assert not a.returncode,(source,a.stderr)
  assert module.read_bytes()==original.read_bytes(),original
  rows.append({'source':str(source.relative_to(r)),'opt':int(opt),'parent':str(original),'sha256':hashlib.sha256(module.read_bytes()).hexdigest(),'status':'identical'})
(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n');assert len(rows)==530,len(rows)
print('PASS',len(rows),'unchanged parent fixture modules')
