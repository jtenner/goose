from pathlib import Path
import json,hashlib
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');rows=[]
for entry in json.loads((p/'parent-module-manifest.json').read_text()):
 assert hashlib.sha256((r/entry['source']).read_bytes()).hexdigest()==entry['source_sha256']
 a=Path(entry['parent_module']).read_bytes();assert hashlib.sha256(a).hexdigest()==entry['parent_sha256'];candidate=p.parent/'full-wasm05/artifacts'/(Path(entry['source']).stem+'-O'+str(entry['opt'])+'.wasm');b=candidate.read_bytes()
 rows.append({**entry,'candidate_module':str(candidate),'candidate_sha256':hashlib.sha256(b).hexdigest(),'parent_bytes':len(a),'candidate_bytes':len(b),'delta_bytes':len(b)-len(a),'identical':a==b})
(p/'module-deltas.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps({'pairs':len(rows),'identical':sum(x['identical'] for x in rows),'changed':sum(not x['identical'] for x in rows),'total_module_delta':sum(x['delta_bytes'] for x in rows),'limit':'Static artifact comparison; no timing or new parent guest execution.'}))
