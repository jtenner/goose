from pathlib import Path
import subprocess,json
from cases import cases
r=Path('/home/dev/Projects/goose-wasm-backend');p=Path(__file__).parent;c=p.parent.parent/'goose-tested';rows=[]
def run(name,args):
 a=subprocess.run(list(map(str,args)),cwd=r,capture_output=True,timeout=90)
 for ext,data in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (p/(name+'.'+ext)).write_bytes(data)
 return a
for name,source in cases.items():
 s=p/(name+'.goose');s.write_text(source+'\n')
 for opt in [0,2]:
  n=name+'-O'+str(opt);native=p/(n+'.native');cs=p/(n+'.c');wasm=p/(n+'.wasm')
  a=run(n+'-native-emit',[c,'-O'+str(opt),'--standalone','-o',cs,s]);assert a.returncode==0,(n,a.stderr)
  a=run(n+'-native-build',['cc','-O0',cs,'-pthread','-lm','-ldl','-o',native]);assert a.returncode==0,(n,a.stderr)
  nativeout=run(n+'-native-run',[native]);assert nativeout.returncode==0,(n,nativeout.stderr)
  a=run(n+'-wasm-emit',[c,'-O'+str(opt),'--target','wasm','-o',wasm,s]);row={'case':name,'opt':opt,'native':nativeout.stdout.decode(),'wasm_emit':a.returncode,'diagnostic':a.stderr.decode()}
  if a.returncode==0:
   a=run(n+'-validate',['wasm-tools','validate',wasm]);assert a.returncode==0,(n,a.stderr)
   for host,args in [('node',['node',r/'scripts/run_wasm.mjs',wasm]),('wasmtime',['/tmp/goose-wasm-runtime-env/bin/python',r/'test/wasmtime_host.py',wasm])]:
    a=run(n+'-'+host,args);row[host]={'exit':a.returncode,'stdout':a.stdout.decode(),'stderr':a.stderr.decode()}
  rows.append(row);(p/'before-results.json').write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps(rows,indent=2))
