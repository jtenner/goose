from pathlib import Path
import hashlib,json,sys
r=Path('/home/dev/Projects/goose-wasm-backend');p=Path(__file__).parent;b=p.parent;before=b/'named-copy-before01';prior=b/'build06/data-named-copy'
sys.path.insert(0,str(r/'test'));from wasm_backend import run,function_local_counts
old=json.loads((before/'results.json').read_text());current=json.loads((prior/'results.json').read_text());assert len(old)==len(current)==32
assert json.loads((prior/'footprint-assertion.json').read_text())['constant_copy_scratch']
rows=[]
for a,c in zip(old,current):
 for k in ['kind','binding','base','amount','opt','source_sha256']:assert a[k]==c[k],k
 stem=f"{a['kind']}-{a['binding']}-{a['base']}-{a['amount']}";name=stem+f"-O{a['opt']}";source=before/(stem+'.goose');assert hashlib.sha256(source.read_bytes()).hexdigest()==a['source_sha256']
 module=p/(name+'.wasm');command=[b/'build06/goose-tested',f"-O{a['opt']}",'--target','wasm','-o',module,source];result=run(command);(p/(name+'-emit.stderr')).write_bytes(result.stderr);(p/(name+'-emit.exit')).write_text(str(result.returncode)+'\n');run(['wasm-tools','validate',module])
 capture=p/(name+'-instance');result=run(['node',r/'test/wasm_reference_abi.mjs',module,capture]);assert result.stdout==b'named-copy=ok\n' and not result.stderr
 files=[]
 for image in (before/(name+'-instance')).glob('*.bin'):
  actual=capture/image.name;assert image.read_bytes()==actual.read_bytes(),(name,image.name)
  files.append({'name':image.name,'before_sha256':hashlib.sha256(image.read_bytes()).hexdigest(),'after_sha256':hashlib.sha256(actual.read_bytes()).hexdigest()})
 assert files
 counts=function_local_counts(module.read_bytes());assert counts==c['locals'],name
 rows.append({'name':name,'source':str(source),'source_sha256':a['source_sha256'],'module_sha256':hashlib.sha256(module.read_bytes()).hexdigest(),'before_module_bytes':a['module_bytes'],'after_module_bytes':module.stat().st_size,'before_locals':a['locals'],'after_locals':counts,'complete_memory_images':files,'Node_oracle':'PASS'})
 (p/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
result={'same_source_paths':True,'whole_image_pairs':len(rows),'all_images':'PASS','retained_native_and_Wasmtime_cases':32,'constant_copy_scratch':'PASS','maximum_locals_before':max(max(x['before_locals']) for x in rows),'maximum_locals_after':max(max(x['after_locals']) for x in rows),'total_module_bytes_before':sum(x['before_module_bytes'] for x in rows),'total_module_bytes_after':sum(x['after_module_bytes'] for x in rows)}
(p/'resolution.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
