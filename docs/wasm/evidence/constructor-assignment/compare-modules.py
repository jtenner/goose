from pathlib import Path
import json,hashlib
r=Path('/home/dev/Projects/goose-wasm-backend');p=Path(__file__).parent;old=Path('/tmp/goose-wasm-fixed-assignment-20261107');before=json.loads((old/'validation-inputs.json').read_text());a=old/'full-correctness01/artifacts';b=p/'full-correctness02/artifacts';rows=[]
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert (p/'full-correctness02/check.exit').read_text().strip()=='0'
for source in sorted((r/'test/wasm').glob('*.goose')):
 key=str(source.relative_to(r))
 if before.get(str(source), before.get(key))!=sha(source):continue
 for opt in (0,2):
  name=source.stem+f'-O{opt}.wasm';parent=a/name;candidate=b/name
  if not parent.exists():continue
  assert candidate.exists() and parent.read_bytes()==candidate.read_bytes(),name
  rows.append({'source':key,'source_sha256':sha(source),'opt':opt,'module_sha256':sha(candidate)})
assert rows, 'no module pairs were checked'
(p/'module-identity.json').write_text(json.dumps({'status':'PASS','parent':'488eeb43718856e6e0332ce8a3a492e917482ced','comparisons':rows},indent=2)+'\n');print('PASS:',len(rows),'unchanged-source parent modules are byte-identical')
