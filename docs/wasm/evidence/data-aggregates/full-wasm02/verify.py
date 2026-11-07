from pathlib import Path
import hashlib,json
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');b=p.parent/'build05'
for manifest in [b/'source-hashes.json',p/'validation-input-hashes.json']:
 for n,h in json.loads(manifest.read_text()).items():assert hashlib.sha256((r/n).read_bytes()).hexdigest()==h,n
assert hashlib.sha256((b/'goose-tested').read_bytes()).hexdigest()=='e1bbd1b28d51382014fe34c1cf93dfff039164286fdb6718f1e27b521b65905c'
for n,h in json.loads((p/'harness-hashes.json').read_text()).items():assert hashlib.sha256((p/n).read_bytes()).hexdigest()==h,n
print('Frozen candidate compiler/source and complete validation inputs match.')

assert hashlib.sha256((p.parent/'resource-unit.py').read_bytes()).hexdigest()=='5d842920156374f1b90c07f1c99f9238e68e566e402c37db37c299739790a9b0'
