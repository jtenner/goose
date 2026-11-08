from pathlib import Path
import json,hashlib,subprocess
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');identity=json.loads((p/'parent-compiler-identity.json').read_text());source=Path('/tmp/goose-wasm-array-expression-source-20261108/build01/source-hashes.json')
assert identity['parent']=='1fae1779b7345fd6a4391d6e3c9bfe617dd775c2'
assert hashlib.sha256(Path(identity['compiler']).read_bytes()).hexdigest()==identity['sha256']
for n,h in json.loads(source.read_text()).items():assert hashlib.sha256(subprocess.check_output(['git','show',identity['parent']+':'+n],cwd=r)).hexdigest()==h,n
rows=json.loads((p/'valid-parent-families.json').read_text());assert len(rows)==46 and len({x['case'] for x in rows})==46
for row in rows:
 name=row['case'];q=p/row['phase'];f=q/(name+'.goose');current=r/'test/wasm'/('wasm_array_prefix_conversion_'+name+'.goose')
 assert f.read_bytes()==current.read_bytes() and hashlib.sha256(f.read_bytes()).hexdigest()==row['source_sha256']
 for k in ['emit','cc','native','wasm']:
  assert int((q/(name+'-'+k+'.exit')).read_text())==row[k+'_exit']
 assert all(row[k+'_exit']==0 for k in ['emit','cc','native']) and row['wasm_exit']==1
 assert not (q/(name+'-native.stderr')).read_bytes()
 assert (q/(name+'-native.stdout')).read_bytes()==(r/'test/expected'/(current.stem+'.out')).read_bytes()
 assert b'array adaptation needs the pending destination lowering' in (q/(name+'-wasm.stderr')).read_bytes()
 assert not (q/(name+'.wasm')).exists()
(p/'parent-verification.json').write_text(json.dumps({'status':'PASS','native_valid_parent_failures':46,'families':rows,'invalid_reference_syntax_preserved':'parent01/reference-emit.stderr','pending_aggregate_layout':'parent03/padded.goose'},indent=2)+'\n');print('PASS 46 native-valid parent failures and exact fixture/golden/compiler identities')
