from pathlib import Path
import subprocess,sys,json,hashlib
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');phase=sys.argv[1];logs=[];rows=[]
exe=Path('/tmp/goose-wasm-inline-ref-abi-20261107/build04/goose-tested') if phase=='parent' else p/'goose-tested'
def run(name,args,ok=True):
 a=subprocess.run([str(x) for x in args],cwd=r,capture_output=True,timeout=180)
 for ext,data in [('stdout',a.stdout),('stderr',a.stderr),('exit',(str(a.returncode)+'\n').encode())]:(p/(name+'.'+ext)).write_bytes(data)
 logs.append({'name':name,'command':[str(x) for x in args],'exit':a.returncode});(p/(phase+'-commands.json')).write_text(json.dumps(logs,indent=2)+'\n')
 if ok:assert a.returncode==0,(name,a.returncode,a.stderr.decode(errors='replace'))
 return a
if phase=='parent':
 reuse=json.loads((p/'verified-parent-reuse.json').read_text())
 for n,h in reuse['files'].items():assert hashlib.sha256((p/n).read_bytes()).hexdigest()==h,n
 rows.extend(reuse['rows'])
for family in ['rows','effects','enums']:
 if phase=='parent' and family=='rows':continue
 stem='wasm_data_aggregate_'+family;source=r/'test/wasm'/(stem+'.goose');expected=(r/'test/expected'/(stem+'.out')).read_bytes()
 for opt in [0,2]:
  name=phase+'-'+family+'-O'+str(opt);module=p/(name+'.wasm')
  if phase=='parent':
   c=p/(name+'.c');native=p/(name+'.native')
   run(name+'-native-emit',[exe,'-O'+str(opt),'--standalone','-o',c,source]);run(name+'-native-build',['cc','-O'+str(opt),c,'-pthread','-lm','-ldl','-o',native]);a=run(name+'-native-run',[native]);assert a.stdout==expected and not a.stderr
   a=run(name+'-admission',[exe,'-O'+str(opt),'--target','wasm','-o',module,source],False)
   assert a.returncode and b'wasm target: compound array elements need the pending layout lowering' in a.stderr and not module.exists(),(name,a.stderr)
  else:
   run(name+'-emit',[exe,'-O'+str(opt),'--target','wasm','-o',module,source]);run(name+'-validate',['wasm-tools','validate',module])
   for engine,command in [('node',['node',r/'test/wasm_reference_abi.mjs',module,p/(name+'-instance')]),('wasmtime',['/tmp/goose-wasm-runtime-env/bin/python',r/'test/wasmtime_host.py',module])]:
    a=run(name+'-'+engine,command);assert a.stdout==expected and not a.stderr,(name,engine,a.stdout,a.stderr)
   run(name+'-wat',['wasm-tools','print',module])
  rows.append({'family':family,'opt':opt,'phase':phase,'expected_output_sha256':hashlib.sha256(expected).hexdigest(),'module_sha256':hashlib.sha256(module.read_bytes()).hexdigest() if module.exists() else None});(p/(phase+'-results.json')).write_text(json.dumps(rows,indent=2)+'\n')
if phase=='candidate':
 helper=p/'memory-runtime';module=p/'memory-runtime.wasm';limited=p/'memory-runtime-limited.wasm'
 run('memory-build',['c++','-std=c++20','-O2',r/'test/wasm_memory.cpp','-o',helper]);run('memory-emit',[helper,module]);run('memory-validate',['wasm-tools','validate',module]);run('memory-node',['node',r/'test/wasm_memory.mjs',module,limited]);run('memory-wasmtime',['/tmp/goose-wasm-runtime-env/bin/python',r/'test/wasm_memory.py',module,limited])
print(phase,':6cases passed;'+('6native references and exact admission failures.' if phase=='parent' else '12engine outcomes plus direct memory helper controls.'))
