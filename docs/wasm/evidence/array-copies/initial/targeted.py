from pathlib import Path
import subprocess,json,hashlib,runpy
r=Path.cwd();p=Path('/tmp/goose-wasm-array-copy-20261107');rows=[]
counts=runpy.run_path(str(r/'test/wasm_backend.py'))['function_local_counts']
def run(name,args):
 args=list(map(str,args));a=subprocess.run(args,cwd=r,capture_output=True,timeout=90)
 for ext,data in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (p/(name+'.'+ext)).write_bytes(data)
 assert a.returncode==0,(name,a.stderr)
 return a
for case in ['values','inline','cleanup']:
 expected=(p/(case+'-O0-native-run.stdout')).read_bytes()
 for opt in [0,2]:
  n=case+'-O'+str(opt);w=p/(n+'.wasm')
  run(n+'-emit',[r/'build/goose','-O'+str(opt),'--target','wasm','-o',w,p/(case+'.goose')])
  run(n+'-validate',['wasm-tools','validate',w])
  for host,args in [('node',['node',r/'scripts/run_wasm.mjs',w]),('wasmtime',['/tmp/goose-wasm-runtime-env/bin/python',r/'test/wasmtime_host.py',w]),('owner',['node',r/'test/wasm_multimemory.mjs',w,'1' if case == 'values' else '0', {'values':'growth','inline':'no-data'}.get(case,'')])]:
   a=run(n+'-'+host,args);assert a.stdout==expected,(n,host,a.stdout,expected)
  lc=counts(w.read_bytes());assert max(lc)<2048,(n,lc)
  rows.append({'case':case,'opt':opt,'bytes':w.stat().st_size,'max_function_locals':max(lc),'sha256':hashlib.sha256(w.read_bytes()).hexdigest()})
(p/'targeted-results.json').write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps(rows))
