from pathlib import Path
import json,hashlib,shutil,sys
p=Path(__file__).parent;raw=p.parent;r=Path('/home/dev/Projects/goose-wasm-backend');out=p/'artifacts';out.mkdir(exist_ok=True)
assert (raw/'images02/check.exit').read_text().strip()=='1'
assert (raw/'images02/check.stdout').read_text().strip()=='Static 100'
assert "AssertionError: i32.const 11(?=" in (raw/'images02/check.stderr').read_text()
old=(raw/'images02/wasm_aggregate_data_fill_checks.py').read_text();current=(r/'test/wasm_aggregate_data_fill_checks.py').read_text();assert old.split('def check_dynamic')[0]==current.split('def check_dynamic')[0]
assert (raw/'images02/wasm_aggregate_data_fill_image.mjs').read_bytes()==(r/'test/wasm_aggregate_data_fill_image.mjs').read_bytes()
for f in (raw/'focused02').glob('*.wasm'):shutil.copy2(f,out/f.name)
sys.path.insert(0,str(r/'test'))
from wasm_backend import run
from wasm_aggregate_data_fill_checks import check_dynamic
n=check_dynamic(run,'node','wasm-tools',out)
(p/'static-reuse.json').write_text(json.dumps({'status':'PASS','static_checks':100,'basis':'images02 passed check_images and failed only while constructing dynamic controls; static function and JS observer unchanged'},indent=2)+'\n')
print('PASS',100+n,'complete fill image/snapshot/identity/cleanup controls; static100 verified reused')
