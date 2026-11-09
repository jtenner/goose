from pathlib import Path
import sys,json,hashlib
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');out=p/'artifacts';out.mkdir(exist_ok=True);sys.path.insert(0,str(r/'test'))
from wasm_backend import run
from wasm_aggregate_data_fill_checks import check_limits
n=check_limits(run,p.parent/'build01/goose-tested','cc','node','wasm-tools',Path('/tmp/goose-wasm-runtime-env/bin/python'),out)
assert n==8
print('PASS8 memory32 count/extent checks; guarded branch prevents huge fill execution')
