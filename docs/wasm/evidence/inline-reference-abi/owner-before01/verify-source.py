from pathlib import Path
import json,hashlib
r=Path('/home/dev/Projects/goose-wasm-backend');p=Path(__file__).parent
for n,h in json.loads((p/'input-hashes.json').read_text()).items():assert hashlib.sha256((r/n).read_bytes()).hexdigest()==h,n
for n in ['test/wasm_reference_abi.mjs','scripts/run_wasm.mjs']:assert hashlib.sha256((p/'before'/n).read_bytes()).hexdigest()==json.loads((p/'input-hashes.json').read_text())[n]
module=p.parent/'build04/candidate/wasm_inline_ref_abi_packed-O0.wasm'
row=next(x for x in json.loads((p.parent/'build04/candidate/case-results.json').read_text()) if x['source'].endswith('wasm_inline_ref_abi_packed.goose') and x['opt']==0)
assert hashlib.sha256(module.read_bytes()).hexdigest()==row['module_sha256']
print('Original observer/adapter and healthy frozen module match.')

for n,h in json.loads((p/'harness-hashes.json').read_text()).items():assert hashlib.sha256((p/n).read_bytes()).hexdigest()==h,n
print('Frozen reproduction harness matches.')
