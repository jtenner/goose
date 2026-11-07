from pathlib import Path
import json,hashlib
p=Path(__file__).parent;old=Path('/tmp/goose-wasm-array-places-20261107/build02');new=p.parent/'full-wasm01/artifacts';rows=[]
for entry in json.loads((old/'prior-modules.json').read_text()):
 stem=Path(entry['source']).stem+'-O'+str(entry['opt']);before=old/(stem+'-after.wasm');after=new/(stem+'.wasm')
 a=before.read_bytes();b=after.read_bytes();assert hashlib.sha256(a).hexdigest()==entry['sha256']
 rows.append({'source':entry['source'],'opt':entry['opt'],'parent_bytes':len(a),'candidate_bytes':len(b),'delta_bytes':len(b)-len(a),'identical':a==b,'parent_sha256':hashlib.sha256(a).hexdigest(),'candidate_sha256':hashlib.sha256(b).hexdigest()})
assert len(rows)==226
(p/'prior-module-deltas.json').write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps({'pairs':len(rows),'identical':sum(x['identical'] for x in rows),'changed':sum(not x['identical'] for x in rows),'aggregate_byte_delta':sum(x['delta_bytes'] for x in rows),'limit':'Read-only artifact comparison; packed ABI changes are expected. Execution evidence is the separate full-suite run.'}))
