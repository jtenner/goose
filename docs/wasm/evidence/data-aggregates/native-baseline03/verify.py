from pathlib import Path
import hashlib,json
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');build=p.parent/'build06'
for name in ['source-hashes.json','input-hashes.json']:
 for n,h in json.loads((build/name).read_text()).items():assert hashlib.sha256((r/n).read_bytes()).hexdigest()==h,n
identity=json.loads((build/'build-identity.json').read_text());assert identity['source_verified'];assert hashlib.sha256((build/'goose-tested').read_bytes()).hexdigest()==identity['compiler_sha256']
for n,h in json.loads((p/'harness-hashes.json').read_text()).items():assert hashlib.sha256((p/n).read_bytes()).hexdigest()==h,n
assert hashlib.sha256((p.parent/'resource-unit.py').read_bytes()).hexdigest()=='5d842920156374f1b90c07f1c99f9238e68e566e402c37db37c299739790a9b0'
print('Final compiler/source/validation inputs and unit wrapper match.')
