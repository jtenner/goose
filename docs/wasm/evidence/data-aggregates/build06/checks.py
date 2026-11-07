from pathlib import Path
import hashlib,json,sys
r=Path('/home/dev/Projects/goose-wasm-backend');p=Path(__file__).parent;b=p.parent
sys.path.insert(0,str(r/'test'))
from wasm_backend import run,function_local_counts
from wasm_data_aggregate_named import check_named_footprint
count=check_named_footprint(run,p/'goose-tested','cc','node','wasm-tools','/tmp/goose-wasm-runtime-env/bin/python',p,function_local_counts)
current=p/'data-named-copy';before=b/'named-copy-before01';rows=json.loads((current/'results.json').read_text());prior=json.loads((before/'results.json').read_text());assert len(rows)==len(prior)==32
for a,c in zip(prior,rows):
 for k in ['kind','binding','base','amount','opt','source_sha256']:assert a[k]==c[k],k
 name=f"{a['kind']}-{a['binding']}-{a['base']}-{a['amount']}-O{a['opt']}-instance"
 for image in (before/name).glob('*.bin'):
  assert image.read_bytes()==(current/name/image.name).read_bytes(),(name,image.name)
result={'check_groups':count,'cases':32,'before_after_complete_memory_images':'PASS','independent_data_models':'PASS','all_engines':'PASS','before_max_locals':max(max(x['locals']) for x in prior),'after_max_locals':max(max(x['locals']) for x in rows),'before_bytes':sum(x['module_bytes'] for x in prior),'after_bytes':sum(x['module_bytes'] for x in rows)}
(p/'named-copy-resolution.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
