from pathlib import Path
import subprocess,json,hashlib
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');exe=p.parent/'build01/goose-tested';rows=[];i=0
def run(args):
 global i
 i+=1;a=subprocess.run(list(map(str,args)),cwd=r,capture_output=True,timeout=120)
 for k,v in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (p/(f'command-{i:04}.'+k)).write_bytes(v)
 (p/f'command-{i:04}.json').write_text(json.dumps(list(map(str,args)))+'\n')
 assert not a.returncode,(args,a.returncode,a.stderr)
 return a
sources=sorted(list((r/'test/wasm').glob('wasm_array_expression_source_*_opaque.goose'))+list((r/'test/wasm').glob('wasm_array_expression_source_*_defer_refs.goose')))
for f in sources:
 name=f.stem
 expected=(r/'test/expected'/(f.stem+'.out')).read_bytes()
 for opt in [0,2]:
  stem=name+f'-O{opt}';c=p/(stem+'.c');native=p/(stem+'.native');wasm=p/(stem+'.wasm')
  run([exe,f'-O{opt}','--standalone','-o',c,f]);run(['cc',f'-O{opt}',c,'-pthread','-lm','-ldl','-o',native]);a=run([native]);assert a.stdout==expected,(name,a.stdout,expected)
  run([exe,f'-O{opt}','--target','wasm','-o',wasm,f]);run(['wasm-tools','validate',wasm])
  for host,args in [('node',['node',r/'scripts/run_wasm.mjs',wasm]),('wasmtime',['/tmp/goose-wasm-runtime-env/bin/python',r/'test/wasmtime_host.py',wasm])]:
   a=run(args);assert a.stdout==expected and not a.stderr,(name,host,a)
  a=run(['node',r/'test/wasm_multimemory.mjs',wasm,'1' if name.endswith('_global') else '0']);assert a.stdout==expected and not a.stderr,(name,a)
  rows.append({'case':name,'opt':opt,'source_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'wasm_sha256':hashlib.sha256(wasm.read_bytes()).hexdigest(),'status':'PASS'})
(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print('PASS',len(rows),'native/Node/Wasmtime positive pairs and completed-owner checks')
