from pathlib import Path
import json,hashlib,sys,subprocess
r=Path('/home/dev/Projects/goose-wasm-backend');p=Path(__file__).parent
for m in ['source-hashes.json','input-hashes.json']:
 for n,h in json.loads((p/m).read_text()).items():assert hashlib.sha256((r/n).read_bytes()).hexdigest()==h,n
parent=Path('/tmp/goose-wasm-array-places-20261107/build02/goose-tested')
assert hashlib.sha256(parent.read_bytes()).hexdigest()=='5b68b041c3aba5c6bd6a6fa7e96a0b5a8aa5cc5558761b56efa5d83cacb1599a'
for n,h in json.loads(Path('/tmp/goose-wasm-array-places-20261107/build02/source-hashes.json').read_text()).items():
 assert hashlib.sha256(subprocess.check_output(['git','show','4c302e7ad2cebaae82ae18a08e9978329cc571a2:'+n],cwd=r)).hexdigest()==h,n
if '--built' in sys.argv:
 ident=json.loads((p/'build-identity.json').read_text());assert ident['source_verified'];assert hashlib.sha256((p/'goose-tested').read_bytes()).hexdigest()==ident['compiler_sha256']
print('Candidate inputs and retained parent provenance match.')

for n,h in json.loads((p/'harness-hashes.json').read_text()).items():assert hashlib.sha256((p.parent/n).read_bytes()).hexdigest()==h,n
print('Frozen unit harness matches.')

control_hash=json.loads((p.parent/'build03/input-hashes.json').read_text())['test/wasm/wasm_inline_ref_abi_packed.goose']
assert hashlib.sha256((p/'rejected-owner-field.goose').read_bytes()).hexdigest()==control_hash
for step in ['native-emit','native-build','native-run']:
 assert (p.parent/'build03/parent'/('wasm_inline_ref_abi_packed-O0-'+step+'.exit')).read_text().strip()=='0'
print('Admission control matches valid native source; thin records are checked before reuse.')
