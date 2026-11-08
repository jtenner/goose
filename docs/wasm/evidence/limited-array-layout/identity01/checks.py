from pathlib import Path
import json,hashlib
p=Path(__file__).parent;raw=p.parent;r=Path('/home/dev/Projects/goose-wasm-backend')
assert (raw/'full-correctness02/check.exit').read_text().strip()=='0'
parent=Path('/tmp/goose-wasm-fixed-array-assignment-layout-20261108/full-correctness01/artifacts');current=raw/'full-correctness02/artifacts';oldhash=json.loads(Path('/tmp/goose-wasm-fixed-array-assignment-layout-20261108/validation-inputs.json').read_text());rows=[]
for source in sorted((r/'test/wasm').glob('*.goose')):
 for opt in [0,2]:
  name=source.stem+f'-O{opt}.wasm';before=parent/name
  if not before.exists():continue
  assert hashlib.sha256(source.read_bytes()).hexdigest()==oldhash[str(source.relative_to(r))]
  after=current/name;assert after.exists() and before.read_bytes()==after.read_bytes(),name
  rows.append({'source':str(source.relative_to(r)),'opt':opt,'parent':str(before),'sha256':hashlib.sha256(after.read_bytes()).hexdigest(),'status':'identical'})
assert len(rows)==1266,len(rows)
(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print('PASS',len(rows),'unchanged Wasm fixture modules,compared from completed full suites')
