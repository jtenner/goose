from pathlib import Path
import hashlib,json,shutil
r=Path('/home/dev/Projects/goose-wasm-backend');p=Path(__file__).parent.parent;c=p/'continuation';old=json.loads((p/'source-manifest.json').read_text());current={f:hashlib.sha256((r/f).read_bytes()).hexdigest() for f in old};changes=[f for f in old if old[f]!=current[f]]
assert changes==['test/wasm_backend.py'],changes
exe=hashlib.sha256((r/'build/goose').read_bytes()).hexdigest();assert exe==hashlib.sha256((p/'goose-tested').read_bytes()).hexdigest()
(c/'source-manifest.json').write_text(json.dumps(current,indent=2)+'\n');(c/'provenance.json').write_text(json.dumps({'compiler_sha256':exe,'changed_after_build':changes,'production_and_adapters_match_build':True},indent=2)+'\n');shutil.copy2(r/'test/wasm_backend.py',c/'final-harness.py');print('Preserved compiler verified;only the test expectation changed.')
