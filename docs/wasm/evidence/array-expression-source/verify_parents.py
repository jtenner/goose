from pathlib import Path
import json,hashlib,subprocess
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');rows=[];invalid=[];guards=[]
parent=json.loads((p/'parent-compiler-identity.json').read_text())
assert parent['parent']=='c423808c123e8b4b89d82f2640838ac86fe2f21c'
assert hashlib.sha256(Path(parent['compiler']).read_bytes()).hexdigest()==parent['sha256']
for n,h in json.loads(Path('/tmp/goose-wasm-limited-array-conversion-20261108/build02/source-hashes.json').read_text()).items():assert hashlib.sha256(subprocess.check_output(['git','show',parent['parent']+':'+n],cwd=r)).hexdigest()==h,n
for phase in ['parent01','parent02','parent03']:
 for row in json.loads((p/phase/'results.json').read_text()):
  name=row['case'];f=p/phase/(name+'.goose');assert hashlib.sha256(f.read_bytes()).hexdigest()==row['source_sha256']
  for k in ['emit','cc','native','wasm']:
   if k+'_exit' in row:assert int((p/phase/(name+'-'+k+'.exit')).read_text())==row[k+'_exit']
  if row['emit_exit']:
   assert name.endswith('_reference_block') and b'copy' in (p/phase/(name+'-emit.stderr')).read_bytes();invalid.append(name);continue
  assert all(row[k+'_exit']==0 for k in ['emit','cc','native'])
  if name.startswith('mixed_'):
   assert row['wasm_exit']==1;guards.append(name);continue
  source=r/'test/wasm'/('wasm_array_expression_source_'+name+'.goose')
  assert f.read_bytes()==source.read_bytes()
  assert (p/phase/(name+'-native.stdout')).read_bytes()==(r/'test/expected'/(source.stem+'.out')).read_bytes()
  assert not (p/phase/(name+'-native.stderr')).read_bytes()
  if row['wasm_exit']==1:
   assert b'pending destination lowering' in (p/phase/(name+'-wasm.stderr')).read_bytes();assert not (p/phase/(name+'.wasm')).exists()
  else:assert row['wasm_exit']==0 and (p/phase/(name+'.wasm')).is_file()
  rows.append({'case':name,'phase':phase,'source_sha256':row['source_sha256'],'parent_wasm_exit':row['wasm_exit'],'status':'native PASS'})
assert len(rows)==30 and sum(x['parent_wasm_exit']==1 for x in rows)==26 and len(invalid)==2 and len(guards)==2
(p/'parent-verification.json').write_text(json.dumps({'status':'PASS','families':rows,'native_valid_parent_failures':26,'parent_supported_regressions':4,'invalid_probes_preserved':invalid,'mixed_layout_parent_rejections':guards},indent=2)+'\n');print('PASS 26 native-valid parent failures,4 supported regressions,2 invalid probes excluded')
