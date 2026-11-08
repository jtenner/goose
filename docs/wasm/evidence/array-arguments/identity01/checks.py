from pathlib import Path
import subprocess,json,hashlib
r=Path('/home/dev/Projects/goose-wasm-backend');p=Path(__file__).parent;exe=p.parent/'build01/goose-tested';parent=Path('/tmp/goose-wasm-fixed-results-20261108/full-correctness02/artifacts');oldhash=json.loads(Path('/tmp/goose-wasm-fixed-results-20261108/selected-validation-inputs.json').read_text());rows=[]
for source in sorted((r/'test/wasm').glob('*.goose')):
 for opt in [0,2]:
  original=parent/(source.stem+f'-O{opt}.wasm')
  if not original.exists():continue
  assert hashlib.sha256(source.read_bytes()).hexdigest()==oldhash[str(source.relative_to(r))]
  module=p/original.name;args=[str(exe),f'-O{opt}','--target','wasm','-o',str(module),str(source)];a=subprocess.run(args,cwd=r,capture_output=True)
  for ext,data in [('stdout',a.stdout),('stderr',a.stderr),('exit',(str(a.returncode)+'\n').encode())]:(p/(module.stem+'.'+ext)).write_bytes(data)
  assert not a.returncode,(source,a.stderr)
  assert module.read_bytes()==original.read_bytes(),original
  rows.append({'source':str(source.relative_to(r)),'opt':opt,'parent':str(original),'sha256':hashlib.sha256(module.read_bytes()).hexdigest(),'status':'identical'})
(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n');assert len(rows)==576,len(rows);print('PASS',len(rows),'unchanged parent fixture modules')
