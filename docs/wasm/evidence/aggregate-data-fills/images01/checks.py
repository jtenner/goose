from pathlib import Path
import sys,shutil,importlib.util
p=Path(__file__).parent;raw=p.parent;r=Path('/home/dev/Projects/goose-wasm-backend');out=p/'artifacts';out.mkdir(exist_ok=True)
for f in (raw/'focused02').glob('*.wasm'):shutil.copy2(f,out/f.name)
sys.path.insert(0,str(r/'test'))
from wasm_backend import run
from wasm_aggregate_data_fill_checks import check_images,check_dynamic
n=check_images(run,'node','wasm-tools',out);print('Static',n,flush=True)
n+=check_dynamic(run,'node','wasm-tools',out);print('PASS',n,'complete fill image/snapshot/identity/cleanup controls')
