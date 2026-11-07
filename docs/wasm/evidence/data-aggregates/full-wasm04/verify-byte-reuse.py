from pathlib import Path
import hashlib,json
p=Path(__file__).parent;a=json.loads((p/'byte-reuse.json').read_text())
for n,h in a['files'].items():assert hashlib.sha256((Path(a['source'])/n).read_bytes()).hexdigest()==h,n
print('Two completed native byte fixture outcomes verified and reused; no rerun.')
