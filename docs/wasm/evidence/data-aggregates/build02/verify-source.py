from pathlib import Path
import hashlib,json,subprocess,sys
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend')
for name in ['source-hashes.json','input-hashes.json']:
 for n,h in json.loads((p/name).read_text()).items():assert hashlib.sha256((r/n).read_bytes()).hexdigest()==h,n
parent=Path('/tmp/goose-wasm-inline-ref-abi-20261107/build04');assert hashlib.sha256((parent/'goose-tested').read_bytes()).hexdigest()=='bcc336c9f3f06f604b6ecdb002f4f355dae24bca9691e5d1b16ca30dfef7148c'
for n,h in json.loads((parent/'source-hashes.json').read_text()).items():assert hashlib.sha256(subprocess.check_output(['git','show','4dc9af871426b6f440f5bdbe7f009531f4d72600:'+n],cwd=r)).hexdigest()==h,n
for n,h in json.loads((p/'harness-hashes.json').read_text()).items():assert hashlib.sha256((p/n).read_bytes()).hexdigest()==h,n
if '--built' in sys.argv:
 identity=json.loads((p/'build-identity.json').read_text());assert identity['source_verified'];assert hashlib.sha256((p/'goose-tested').read_bytes()).hexdigest()==identity['compiler_sha256']
print('Frozen candidate source/inputs and retained parent Git source/compiler identities match.')
