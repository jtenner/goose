from pathlib import Path
import json,hashlib
p=Path(__file__).parent;raw=p.parent;cases=json.loads((raw/'cases02.json').read_text());rows=[]
for n,text in cases.items():
 d=raw/('parent04' if n in ['nested','array'] else 'parent01');f=d/(n+'.goose');assert f.read_text()==text+'\n'
 for phase in ['emit','cc','native']:assert (d/(n+'-'+phase+'.exit')).read_text().strip()=='0'
 assert (d/(n+'-native.stdout')).read_bytes()==n.encode()+b'\n'
 assert (d/(n+'-wasm.exit')).read_text().strip()=='1' and not (d/(n+'.wasm')).exists()
 reason=(d/(n+'-wasm.stderr')).read_text();expected={'element':'compound array elements need the pending layout lowering','array':'compound array elements need the pending layout lowering','zero':'zero-sized aggregate results need the pending call lowering'}.get(n,'fixed negation needs an exact source layout')
 assert expected in reason,(n,reason)
 rows.append({'case':n,'source':str(f),'source_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'native':'PASS','wasm_expected':expected,'scope':'separate existing guard' if n in ['element','array','zero'] else 'negation adaptation','reused':str(d)})
(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print('PASS10native-valid cases;7negation failures/3separate guards;no compiler or guest rerun')
