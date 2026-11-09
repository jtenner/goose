from pathlib import Path
import sys,shutil
p=Path(__file__).parent;raw=p.parent;r=Path('/home/dev/Projects/goose-wasm-backend');out=p/'artifacts';out.mkdir(exist_ok=True)
for f in (raw/'focused02').glob('*.wasm'):shutil.copy2(f,out/f.name)
sys.path.insert(0,str(r/'test'))
from wasm_backend import run
from wasm_aggregate_leb_checks import check_sizes
n=check_sizes(run,'node','wasm-tools',out);assert n==8;print('PASS8 LEB product/sum preallocation guards and precise controls')
