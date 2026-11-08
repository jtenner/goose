from pathlib import Path
import json,hashlib
p=Path(__file__).parent
rows=json.loads((p/'results.json').read_text())
assert len(rows)==5
for row in rows:
 n=row['case'];assert hashlib.sha256((p/(n+'.goose')).read_bytes()).hexdigest()==row['source_sha256']
 for kind in ['emit','cc','native']:
  assert row[kind+'_exit']==0 and (p/(n+'-'+kind+'.exit')).read_text().strip()=='0'
 assert row['wasm_exit']==1 and (p/(n+'-wasm.exit')).read_text().strip()=='1'
 assert (p/(n+'-native.stdout')).read_bytes()==(n+'\n').encode()
 assert b'pending destination lowering' in (p/(n+'-wasm.stderr')).read_bytes()
 assert not (p/(n+'.wasm')).exists()
print('PASS 5 native-valid parent failures; source/status/output/module-absence records checked')
