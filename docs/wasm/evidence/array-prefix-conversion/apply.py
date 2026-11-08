from pathlib import Path
import hashlib,json,subprocess,shutil
r=Path('/home/dev/Projects/goose-wasm-backend');p=Path(__file__).parent
assert not subprocess.check_output(['git','status','--porcelain'],cwd=r).strip(),'commit prior increment first'
inputs=json.loads((p/'patch-inputs.json').read_text())
for n,h in inputs.items():assert hashlib.sha256((r/n).read_bytes()).hexdigest()==h,n
parent=subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()
for n in ['wasm_arrays.h','wasm_codegen.h']:shutil.copy2(p/('proposed-'+n),r/'src'/n)
rows=[]
for phase in ['parent01','parent02','parent03','parent04','parent06']:
 for row in json.loads((p/phase/'results.json').read_text()):
  if row.get('native_exit')!=0 or row.get('wasm_exit')!=1 or row['case']=='reference_index':continue
  name=row['case'];source=p/phase/(name+'.goose');assert hashlib.sha256(source.read_bytes()).hexdigest()==row['source_sha256']
  out=r/'test/wasm'/('wasm_array_prefix_conversion_'+name+'.goose');out.write_bytes(source.read_bytes());(r/'test/expected'/(out.stem+'.out')).write_bytes((p/phase/(name+'-native.stdout')).read_bytes());rows.append(dict(row,phase=phase))
assert len(rows)==46 and len({x['case'] for x in rows})==46
(p/'valid-parent-families.json').write_text(json.dumps(rows,indent=2)+'\n')
identity=json.loads((p/'parent-compiler-identity.json').read_text());identity['parent']=parent;(p/'parent-compiler-identity.json').write_text(json.dumps(identity,indent=2)+'\n')
p.joinpath('focused01').mkdir(exist_ok=True)
s=Path('/tmp/goose-wasm-array-expression-source-20261108/focused01/checks.py').read_text().replace('/tmp/goose-wasm-array-expression-source-20261108','/tmp/goose-wasm-array-prefix-conversion-20261108').replace('wasm_array_expression_source_','wasm_array_prefix_conversion_').replace("'1' if name.endswith('_global') else '0'","'2' if name.endswith('_global') else '0'")
(p/'focused01/checks.py').write_text(s)
print('applied two-header patch and46native-valid fixtures; parent',parent)
