from pathlib import Path
import hashlib,json,subprocess,shutil
r=Path('/home/dev/Projects/goose-wasm-backend');p=Path(__file__).parent
assert not subprocess.check_output(['git','status','--porcelain'],cwd=r).strip()
for n,h in json.loads((p/'patch-inputs.json').read_text()).items():assert hashlib.sha256((r/n).read_bytes()).hexdigest()==h,n
parent=subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()
for n in ['wasm_arrays.h','wasm_support.h']:shutil.copy2(p/('proposed-'+n),r/'src'/n)
rows=[]
for phase in ['parent01','parent02','parent03']:
 for row in json.loads((p/phase/'results.json').read_text()):
  assert all(row[k+'_exit']==0 for k in ['emit','cc','native']) and row['wasm_exit']==1,row
  name=row['case'];f=p/phase/(name+'.goose');assert hashlib.sha256(f.read_bytes()).hexdigest()==row['source_sha256']
  out=r/'test/wasm'/('wasm_aggregate_prefix_'+name+'.goose');out.write_bytes(f.read_bytes());(r/'test/expected'/(out.stem+'.out')).write_bytes((p/phase/(name+'-native.stdout')).read_bytes());rows.append(dict(row,phase=phase))
assert len(rows)==53
(p/'valid-parent-families.json').write_text(json.dumps(rows,indent=2)+'\n');identity=json.loads((p/'parent-compiler-identity.json').read_text());identity['parent']=parent;(p/'parent-compiler-identity.json').write_text(json.dumps(identity,indent=2)+'\n')
q=p/'build01';q.mkdir(exist_ok=True);(q/'source-hashes.json').write_text(json.dumps({str(f.relative_to(r)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted((r/'src').rglob('*')) if f.is_file()},indent=2)+'\n')
q=p/'focused01';q.mkdir(exist_ok=True);s=Path('/tmp/goose-wasm-array-prefix-conversion-20261108/focused02/checks.py').read_text().replace('wasm_array_prefix_conversion_','wasm_aggregate_prefix_').replace("'2' if name.endswith('_global') else '0'","'1' if name.endswith('_global') else '0'");(q/'checks.py').write_text(s)
print('applied two-header patch and53native-valid rejecting families; parent',parent)
