from pathlib import Path
import hashlib,json
p=Path(__file__).parent.parent;r=Path('/home/dev/Projects/goose-wasm-backend')
for n,h in json.loads((p/'build02/source-hashes.json').read_text()).items():
 if n.startswith('src/') or n=='CMakeLists.txt':assert hashlib.sha256((r/n).read_bytes()).hexdigest()==h,n
assert hashlib.sha256((p/'build02/goose-tested').read_bytes()).hexdigest()=='bd3856b6c2eedd69bd4eaf343aa9f505794f1a17ab3383194b218fbe33fa368d'
print('Frozen compiler/source identity matches.')
