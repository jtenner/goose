from pathlib import Path
import json,hashlib,subprocess
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');out=[]
parent=json.loads((p/'parent-source.json').read_text());assert parent['parent']=='ca0a5a7b5c0f105d742fa1cdc9e16c488a7b4da3'
assert hashlib.sha256(Path(parent['compiler']).read_bytes()).hexdigest()==parent['sha256']
for n,h in json.loads(Path('/tmp/goose-wasm-limited-array-layout-20261108/build02/source-hashes.json').read_text()).items():assert hashlib.sha256(subprocess.check_output(['git','show',parent['parent']+':'+n],cwd=r)).hexdigest()==h,n
for phase in ['parent01','parent02','parent03']:
 for row in json.loads((p/phase/'results.json').read_text()):
  name=row['case'];f=p/phase/(name+'.goose');source=r/'test/wasm'/('wasm_limited_array_conversion_'+name+'.goose')
  assert f.read_bytes()==source.read_bytes();assert hashlib.sha256(f.read_bytes()).hexdigest()==row['source_sha256']
  assert all(row[k+'_exit']==0 for k in ['emit','cc','native']);assert row['wasm_exit']==1
  assert not (p/phase/(name+'-native.stderr')).read_bytes()
  assert (p/phase/(name+'-native.stdout')).read_bytes()==(r/'test/expected'/(source.stem+'.out')).read_bytes()
  assert b'pending destination lowering' in (p/phase/(name+'-wasm.stderr')).read_bytes();assert not (p/phase/(name+'.wasm')).exists()
  out.append({'case':name,'phase':phase,'source_sha256':row['source_sha256'],'status':'native PASS / parent Wasm rejected'})
assert len(out)==55 and len({x['case'] for x in out})==55
(p/'parent-verification.json').write_text(json.dumps({'status':'PASS','families':out,'reused_original_parent_producers':46,'fresh_extra_parent_producers':9},indent=2)+'\n');print('PASS',len(out),'native-valid parent failures and exact fixture/golden hashes')
