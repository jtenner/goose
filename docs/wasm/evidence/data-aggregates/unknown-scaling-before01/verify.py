from pathlib import Path
import hashlib,json
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');b=p.parent
assert hashlib.sha256((b/'build04/goose-tested').read_bytes()).hexdigest()=='e1eacdffc85c2f042b72127579ea332a5426384e373478b571c859f98c87ea42'
for n,h in json.loads((b/'build04/source-hashes.json').read_text()).items():assert hashlib.sha256((b/'e1-source-reconstruction'/n).read_bytes()).hexdigest()==h,n
for n,h in json.loads((p/'inputs.json').read_text()).items():assert hashlib.sha256((r/n).read_bytes()).hexdigest()==h,n
for n,h in json.loads((p/'harness-hashes.json').read_text()).items():assert hashlib.sha256((p/n).read_bytes()).hexdigest()==h,n
print('Retained E1 compiler/source reconstruction and unchanged test inputs match.')
