from pathlib import Path
import subprocess,sys,json
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');sys.path.insert(0,str(r/'test'))
from wasm_array_result_checks import check_guards
import wasm_aggregate_admission as aggregate
aggregate.CASES={k:v for k,v in aggregate.CASES.items() if k=='adaptation'}
from wasm_array_copy_admission import CASES,reason

i=0
records=[]
def run(args,ok=True):
 global i
 i+=1;a=subprocess.run(list(map(str,args)),cwd=r,capture_output=True,timeout=120)
 for k,v in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (p/(f'command-{i:04}.'+k)).write_bytes(v)
 (p/f'command-{i:04}.json').write_text(json.dumps(list(map(str,args)))+'\n')
 if ok:assert not a.returncode,(args,a.stderr)
 return a
out=p/'artifacts';out.mkdir(exist_ok=True);exe=p.parent/'build01/goose-tested'
count=check_guards(run,exe,'cc',out,'node','wasm-tools','/tmp/goose-wasm-runtime-env/bin/python')
count+=aggregate.check_admission(run,exe,'cc','node','wasm-tools','/tmp/goose-wasm-runtime-env/bin/python',out)
for name in ['fixed-limited','ref-fixed-limited','call-layout','inline-call-layout','indexed-layout']:
 source=out/(name+'.goose');source.write_text(CASES[name])
 for opt in [0,2]:
  c=out/(name+f'-O{opt}.c');native=c.with_suffix('.native');wasm=c.with_suffix('.wasm')
  run([exe,f'-O{opt}','--standalone','-o',c,source]);run(['cc',c,'-pthread','-lm','-ldl','-o',native]);a=run([native]);assert a.stdout==b'3,1\n'
  run([exe,f'-O{opt}','--target','wasm','-o',wasm,source]);run(['wasm-tools','validate',wasm])
  for args in [['node',r/'scripts/run_wasm.mjs',wasm],['/tmp/goose-wasm-runtime-env/bin/python',r/'test/wasmtime_host.py',wasm]]:
   a=run(args);assert a.stdout==b'3,1\n' and not a.stderr
  count+=1
assert count==18,count
(p/'results.json').write_text(json.dumps({'checks':count},indent=2)+'\n');print('PASS',count,'updated guards and retained nonfixed result rejection')
