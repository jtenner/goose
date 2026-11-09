from pathlib import Path
import sys,shutil
p=Path(__file__).parent;raw=p.parent;r=Path('/home/dev/Projects/goose-wasm-backend');out=p/'artifacts';out.mkdir(exist_ok=True)
for f in (raw/'focused02').glob('*.wasm'):shutil.copy2(f,out/f.name)
sys.path.insert(0,str(r/'test'))
from wasm_backend import run
from wasm_aggregate_leb_checks import check_fill_images,check_copy_images,check_guards
n=check_fill_images(run,'node','wasm-tools',out);print('Fill',n,flush=True)
n+=check_copy_images(run,'node','wasm-tools',out);print('Images',n,flush=True)
n+=check_guards(run,raw/'build01/goose-tested','cc',out);print('PASS',n,'LEB fill/copy images, precise controls and retained guards')
