from pathlib import Path
import json,hashlib
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');proof=[]
for stage in ['parent01','parent02','parent03','parent04']:
 for row in json.loads((p/stage/'results.json').read_text()):
  n=row['case'];f=p/stage/(n+'.goose');sha=hashlib.sha256(f.read_bytes()).hexdigest()
  assert sha==row['source_sha256']
  fixture=r/'test/wasm'/('wasm_fixed_array_assignment_layout_'+n+'.goose');assert hashlib.sha256(fixture.read_bytes()).hexdigest()==sha,n
  for kind in ['emit','cc','native']:assert (p/stage/(n+'-'+kind+'.exit')).read_text().strip()=='0',(stage,n,kind)
  assert (p/stage/(n+'-wasm.exit')).read_text().strip()=='1'
  assert not (p/stage/(n+'.wasm')).exists()
  assert b'whole-array assignment adaptation needs the pending destination lowering' in (p/stage/(n+'-wasm.stderr')).read_bytes()
  assert (p/stage/(n+'-native.stdout')).read_bytes()==(r/'test/expected'/(fixture.stem+'.out')).read_bytes()
  assert not (p/stage/(n+'-native.stderr')).read_bytes()
  proof.append({'case':n,'source_sha256':sha,'parent_stage':stage,'native':'PASS','parent_wasm':'specific rejection'})
assert len(proof)==21 and len({x['case'] for x in proof})==21
(p/'parent-verification.json').write_text(json.dumps({'status':'PASS','families':proof},indent=2)+'\n');print('PASS 21 native-valid parent failures and exact fixture hashes')
