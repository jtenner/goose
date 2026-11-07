from pathlib import Path
import hashlib,json
root=Path(__file__).parent.parent;r=Path('/home/dev/Projects/goose-wasm-backend')
for n,h in json.loads((root/'build01/source-hashes.json').read_text()).items():assert hashlib.sha256((r/n).read_bytes()).hexdigest()==h,n
assert hashlib.sha256((root/'build01/goose-tested').read_bytes()).hexdigest()=='c9519e59d47ea996b84d249fee688704bfab0ed49cf5c1ef844e7daf3bdd60d2'
print('Preserved compiler and frozen source match.')
