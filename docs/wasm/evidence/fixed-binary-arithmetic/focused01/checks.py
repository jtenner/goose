from pathlib import Path
import json,subprocess,hashlib
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');exe=p.parent/'build01/goose-tested';rows=[];i=0
parent={x['case']:x for x in json.loads((p.parent/'parent01/results.json').read_text())}
def run(args):
 global i
 i+=1;a=subprocess.run(list(map(str,args)),cwd=r,capture_output=True,timeout=120)
 for k,v in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (p/(f'command-{i:04}.'+k)).write_bytes(v)
 (p/f'command-{i:04}.json').write_text(json.dumps(list(map(str,args)))+'\n');assert not a.returncode,(args,a.stderr)
 return a
for n in json.loads((p.parent/'cases.json').read_text()):
 f=p.parent/'parent01'/(n+'.goose');assert hashlib.sha256(f.read_bytes()).hexdigest()==parent[n]['source_sha256'] and parent[n]['native']=='PASS'
 expected=n.encode()+b'\n'
 for opt in [0,2]:
  module=p/(n+f'-O{opt}.wasm');run([exe,f'-O{opt}','--target','wasm','-o',module,f]);run(['wasm-tools','validate',module])
  for host,args in [('node',['node',r/'scripts/run_wasm.mjs',module]),('wasmtime',['/tmp/goose-wasm-runtime-env/bin/python',r/'test/wasmtime_host.py',module])]:
   a=run(args);assert a.stdout==expected and not a.stderr,(n,opt,host,a)
  a=run(['node',r/'test/wasm_multimemory.mjs',module,'0','no-data']);assert a.stdout==expected and not a.stderr,(n,opt,a)
  rows.append({'case':n,'opt':opt,'source_sha256':parent[n]['source_sha256'],'wasm_sha256':hashlib.sha256(module.read_bytes()).hexdigest(),'status':'PASS'})
(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print('PASS',len(rows),'Native-first/Node/Wasmtime positive pairs and completed-owner checks')
