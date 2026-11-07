from pathlib import Path
import hashlib,json
r=Path('/home/dev/Projects/goose-wasm-backend');p=Path(__file__).parent;b=p.parent/'build04'
for manifest in [b/'source-hashes.json',p.parent/'validation-input-hashes-v3.json']:
 for n,h in json.loads(manifest.read_text()).items():assert hashlib.sha256((r/n).read_bytes()).hexdigest()==h,n
assert hashlib.sha256((b/'goose-tested').read_bytes()).hexdigest()=='bcc336c9f3f06f604b6ecdb002f4f355dae24bca9691e5d1b16ca30dfef7148c'
assert json.loads((b/'build-identity.json').read_text())['source_verified']
print('Frozen ABI compiler, source and validation inputs match.')
