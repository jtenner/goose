from pathlib import Path
import hashlib,json,shutil
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend')
for n,h in json.loads((p/'source-hashes.json').read_text()).items():assert hashlib.sha256((r/n).read_bytes()).hexdigest()==h,n
exe=p/'goose-tested';assert not exe.exists();shutil.copy2(r/'build/goose',exe)
(p/'build-identity.json').write_text(json.dumps({'compiler_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'source_verified':True,'parent':'4dc9af871426b6f440f5bdbe7f009531f4d72600'},indent=2)+'\n')
