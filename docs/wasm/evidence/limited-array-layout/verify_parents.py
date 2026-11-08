from pathlib import Path
import json,hashlib
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');candidates={};invalid=[]
for phase in ['parent01','parent02','parent03','parent04','parent05','parent06']:
 for row in json.loads((p/phase/'results.json').read_text()):
  name=row['case'];f=p/phase/(name+'.goose')
  assert hashlib.sha256(f.read_bytes()).hexdigest()==row['source_sha256']
  if row.get('native_exit')!=0:
   assert row['emit_exit']!=0;invalid.append({'phase':phase,'case':name,'reason':(p/phase/(name+'-emit.stderr')).read_text()});continue
  assert all(row[x+'_exit']==0 for x in ['emit','cc','native'])
  assert row['wasm_exit']==1
  assert b'pending destination lowering' in (p/phase/(name+'-wasm.stderr')).read_bytes()
  assert not (p/phase/(name+'.wasm')).exists()
  actual=r/'test/wasm'/('wasm_limited_array_layout_'+name+'.goose')
  assert f.read_bytes()==actual.read_bytes()
  expected=(r/'test/expected'/(actual.stem+'.out')).read_bytes()
  assert (p/phase/(name+'-native.stdout')).read_bytes()==expected
  assert not (p/phase/(name+'-native.stderr')).read_bytes()
  candidates[name]={'case':name,'phase':phase,'source_sha256':row['source_sha256'],'parent_native':'PASS','parent_wasm':'rejected adaptation'}
assert len(candidates)==32,len(candidates)
(p/'parent-verification.json').write_text(json.dumps({'status':'PASS','families':list(candidates.values()),'invalid_fixtures_preserved':invalid},indent=2)+'\n')
print('PASS',len(candidates),'native-valid parent failures;',len(invalid),'invalid attempts preserved')
