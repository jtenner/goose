from pathlib import Path
import sys
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');out=p/'artifacts';out.mkdir(exist_ok=True);sys.path.insert(0,str(r/'test'))
from wasm_backend import run
import wasm_aggregate_admission as m
m.CASES={'data-varint':m.CASES['data-varint']}
n=m.check_admission(run,p.parent/'build01/goose-tested','cc',out,'node','wasm-tools',Path('/tmp/goose-wasm-runtime-env/bin/python'))
assert n==2;print('PASS2 retained nested-field LEB native/Node/Wasmtime/owner cases')
