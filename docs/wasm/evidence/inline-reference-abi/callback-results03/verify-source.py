from pathlib import Path
import json,hashlib
r=Path('/home/dev/Projects/goose-wasm-backend');p=Path(__file__).parent
for n,h in json.loads((p/'input-hashes.json').read_text()).items():assert hashlib.sha256((r/n).read_bytes()).hexdigest()==h,n
for n,h in json.loads((p.parent/'build04/source-hashes.json').read_text()).items():assert hashlib.sha256((r/n).read_bytes()).hexdigest()==h,n
for binary,h in [(Path('/tmp/goose-wasm-array-places-20261107/build02/goose-tested'),'5b68b041c3aba5c6bd6a6fa7e96a0b5a8aa5cc5558761b56efa5d83cacb1599a'),(p.parent/'build04/goose-tested','bcc336c9f3f06f604b6ecdb002f4f355dae24bca9691e5d1b16ca30dfef7148c')]:assert hashlib.sha256(binary.read_bytes()).hexdigest()==h
for n,h in json.loads((p/'harness-hashes.json').read_text()).items():assert hashlib.sha256((p/n).read_bytes()).hexdigest()==h,n
print('Callback fixtures, corrected adapter and both frozen compilers match.')
