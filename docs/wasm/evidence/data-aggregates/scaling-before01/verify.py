from pathlib import Path
import json,hashlib
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');b=p.parent/'build04'
for n,h in json.loads((b/'source-hashes.json').read_text()).items():assert hashlib.sha256((r/n).read_bytes()).hexdigest()==h,n
assert hashlib.sha256((b/'goose-tested').read_bytes()).hexdigest()=='e1eacdffc85c2f042b72127579ea332a5426384e373478b571c859f98c87ea42'
for n,h in json.loads((p/'inputs.json').read_text()).items():assert hashlib.sha256((r/n).read_bytes()).hexdigest()==h,n
for n,h in json.loads((p/'harness-hashes.json').read_text()).items():assert hashlib.sha256((p/n).read_bytes()).hexdigest()==h,n
print('Preserved candidate compiler/source and scaling harness match.')
