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
sources=[r/'test/wasm'/('wasm_fixed_array_conversion_'+n+'.goose') for n in ['owner_variable', 'owner_varint', 'owner_limited', 'owner_grow', 'owner_stored', 'prefix_0', 'prefix_127', 'prefix_128', 'prefix_16383', 'prefix_16384', 'operators', 'effects', 'scalar_order', 'readonly', 'defer_result', 'early_return', 'early_continue', 'function_data', 'zero_effects', 'large_growth', 'padded_data', 'default_effects']]
for f in sources:
 name=f.stem
 expected=(r/'test/expected'/(f.stem+'.out')).read_bytes()
 for opt in [0,2]:
  stem=name+f'-O{opt}';c=p/(stem+'.c');native=p/(stem+'.native');wasm=p/(stem+'.wasm')
  run([exe,f'-O{opt}','--standalone','-o',c,f]);run(['cc',c,'-pthread','-lm','-ldl','-o',native]);a=run([native]);assert a.stdout==expected,(name,a.stdout,expected)
  run([exe,f'-O{opt}','--target','wasm','-o',wasm,f]);run(['wasm-tools','validate',wasm])
  for host,args in [('node',['node',r/'scripts/run_wasm.mjs',wasm]),('wasmtime',['/tmp/goose-wasm-runtime-env/bin/python',r/'test/wasmtime_host.py',wasm])]:
   a=run(args);assert a.stdout==expected and not a.stderr,(name,host,a)
  a=run(['node',r/'test/wasm_multimemory.mjs',wasm,'1' if name=='wasm_fixed_array_conversion_global' else '0']);assert a.stdout==expected and not a.stderr,(name,a)
  rows.append({'case':name,'opt':opt,'source_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'wasm_sha256':hashlib.sha256(wasm.read_bytes()).hexdigest(),'status':'PASS'})
(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print('PASS',len(rows),'native/Node/Wasmtime positive pairs and completed-owner checks')
