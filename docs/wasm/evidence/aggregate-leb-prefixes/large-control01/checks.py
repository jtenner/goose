from pathlib import Path
import subprocess,json,hashlib
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');file=p.parent/'images01/artifacts/wasm_aggregate_leb_image_fill16383-O0-short.wasm';observer=r/'test/wasm_aggregate_leb_fill_image.mjs'
a=subprocess.run(['node',str(observer),str(file),'16383'],capture_output=True,timeout=90)
(p/'producer.stdout').write_bytes(a.stdout);(p/'producer.stderr').write_bytes(a.stderr);(p/'producer.exit').write_text(str(a.returncode)+'\n')
assert a.returncode==1 and b'LEB fill data image differs' in a.stderr,a.stderr
(p/'identity.json').write_text(json.dumps({'mutant_sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'observer_sha256':hashlib.sha256(observer.read_bytes()).hexdigest(),'status':'PASS expected full-image assertion'},indent=2)+'\n')
print('PASS unchanged short-copy mutant fails its specific full-buffer assertion')
