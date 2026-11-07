from pathlib import Path
import hashlib,json,sys
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend')
for manifest in ['source-hashes.json','input-hashes.json']:
 for n,h in json.loads((p/manifest).read_text()).items():assert hashlib.sha256((r/n).read_bytes()).hexdigest()==h,n
for n,h in json.loads((p/'harness-hashes.json').read_text()).items():assert hashlib.sha256((p/n).read_bytes()).hexdigest()==h,n
if '--built' in sys.argv:assert hashlib.sha256((p/'goose-tested').read_bytes()).hexdigest()==json.loads((p/'build-identity.json').read_text())['compiler_sha256']
print('Frozen one-file compiler repair and validation inputs match.')
