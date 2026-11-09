from pathlib import Path
import subprocess,json,hashlib
p=Path(__file__).parent;raw=p.parent;r=Path('/home/dev/Projects/goose-wasm-backend');exe=raw/'build01/goose-tested';rows=[];i=0
def run(args):
 global i
 i+=1;args=list(map(str,args));a=subprocess.run(args,cwd=r,capture_output=True,timeout=120)
 (p/f'command-{i:04}.json').write_text(json.dumps(args)+'\n')
 for k,v in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (p/f'command-{i:04}.{k}').write_bytes(v)
 assert not a.returncode,(args,a.returncode,a.stderr)
 return a
for record in json.loads((raw/'exact-positive-families.json').read_text()):
 name=record['fixture'];f=r/'test/wasm'/(name+'.goose');expected=record['expected'].encode();assert hashlib.sha256(f.read_bytes()).hexdigest()==record['source_sha256']
 for opt in (0,2):
  stem=p/(name+f'-O{opt}');c,native,wasm=[stem.with_suffix(ext) for ext in ['.c','.native','.wasm']]
  run([exe,f'-O{opt}','--standalone','-o',c,f]);run(['cc',f'-O{opt}',c,'-pthread','-lm','-ldl','-o',native]);a=run([native]);assert a.stdout==expected and not a.stderr,(name,a.stdout,a.stderr)
  run([exe,f'-O{opt}','--target','wasm','-o',wasm,f]);run(['wasm-tools','validate',wasm])
  for host,args in [('node',['node',r/'test/wasm_reference_abi.mjs',wasm,p/(name+f'-O{opt}-instance')]),('wasmtime',['/tmp/goose-wasm-runtime-env/bin/python',r/'test/wasmtime_host.py',wasm]),('owner',['node',r/'test/wasm_multimemory.mjs',wasm,'2' if name.endswith('_global') else '0'])]:
   a=run(args);assert a.stdout==expected and not a.stderr,(name,opt,host,a.stdout,a.stderr)
  rows.append({'case':name,'opt':opt,'source_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'wasm_sha256':hashlib.sha256(wasm.read_bytes()).hexdigest(),'status':'PASS'})
  (p/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
print('PASS',len(rows),'native/Node/Wasmtime pairs and completed-owner checks')
