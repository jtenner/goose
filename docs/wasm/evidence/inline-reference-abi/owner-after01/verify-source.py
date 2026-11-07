from pathlib import Path
import hashlib,json
r=Path('/home/dev/Projects/goose-wasm-backend');p=Path(__file__).parent
for n,h in json.loads((p/'input-hashes.json').read_text()).items():assert hashlib.sha256((r/n).read_bytes()).hexdigest()==h,n
for n,h in json.loads((p.parent/'build04/source-hashes.json').read_text()).items():assert hashlib.sha256((r/n).read_bytes()).hexdigest()==h,n
for n in ['test/wasm_reference_abi.mjs','scripts/run_wasm.mjs']:assert (r/n).read_bytes()==(p/'before'/n).read_bytes()
assert (p/'before-check.py').read_bytes()==(p.parent/'owner-before01/before-check.py').read_bytes()
for n in ['print-owner.wasm','snapshot-owner.wasm','controls.json']:assert (p/'controls'/n).read_bytes()==(p.parent/'owner-before01/controls'/n).read_bytes()
for n,h in json.loads((p/'harness-hashes.json').read_text()).items():assert hashlib.sha256((p/n).read_bytes()).hexdigest()==h,n
print('Corrected observer snapshots, unchanged compiler source, same acceptance checks and validated controls match.')
