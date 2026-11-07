from pathlib import Path
import hashlib,json
r=Path('/home/dev/Projects/goose-wasm-backend');root=Path(__file__).parent.parent
for name,digest in json.loads((root/'build02/source-hashes.json').read_text()).items():
 if name.startswith('src/') or name=='CMakeLists.txt':assert hashlib.sha256((r/name).read_bytes()).hexdigest()==digest,name
assert hashlib.sha256((root/'build02/goose-tested').read_bytes()).hexdigest()=='250902481fe28fadfd7102f7ac64475814c864dbc91ff2060ce5b9ed360eb73c'
print('Frozen compiler/source identity matches.')
