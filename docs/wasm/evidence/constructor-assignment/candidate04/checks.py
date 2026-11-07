from pathlib import Path
import subprocess,json,hashlib,sys
r=Path('/home/dev/Projects/goose-wasm-backend');root=Path('/tmp/goose-wasm-constructor-assignment-20261107');p=Path(__file__).parent;exe=root/'build04/goose-tested';rows=[];commands=[]
sys.path.insert(0,str(r/'test'));from wasm_constructor_assignment_checks import check_owners,check_failure,check_target_failure

def run(args,ok=True):
 a=subprocess.run([str(x) for x in args],cwd=r,capture_output=True,timeout=120);name=f'command{len(commands):04}'
 for ext,data in [('stdout',a.stdout),('stderr',a.stderr),('exit',(str(a.returncode)+'\n').encode())]:(p/(name+'.'+ext)).write_bytes(data)
 commands.append({'name':name,'args':[str(x) for x in args],'exit':a.returncode});(p/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
 if ok:assert not a.returncode,(name,args,a.returncode,a.stdout,a.stderr)
 return a
old=[]
for folder in ['parent-first','parent-extra02','target-parent','aggregate-parent','exits-parent','more-parent']:old+=json.loads((root/folder/'results.json').read_text())
for source in sorted((r/'test/wasm').glob('wasm_constructor_assignment_*.goose')):
 name=source.stem.removeprefix('wasm_constructor_assignment_').replace('variant_empty','variant-empty');previous=[x for x in old if x['case']==name];assert len(previous)==2,(name,previous)
 assert all(x['source_sha256']==hashlib.sha256(source.read_bytes()).hexdigest() for x in previous)
 expected=(r/'test/expected'/(source.stem+'.out')).read_bytes()
 for opt in [0,2]:
  module=p/(source.stem+f'-O{opt}.wasm')
  run([exe,f'-O{opt}','--target','wasm','-o',module,source]);run(['wasm-tools','validate',module])
  for engine,args in [('node',['node',r/'scripts/run_wasm.mjs',module]),('wasmtime',['/tmp/goose-wasm-runtime-env/bin/python',r/'test/wasmtime_host.py',module])]:
   a=run(args);assert a.stdout==expected and not a.stderr,(name,opt,engine,a.stdout,a.stderr)
  rows.append({'case':name,'opt':opt,'native_reused':previous,'node':'PASS','wasmtime':'PASS'});(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
print('PASS:',len(rows),'constructor cases, both Wasm engines, native outputs reused by source hash.')
print('PASS:',check_owners(run,'node','wasm-tools',p),'live owner/control groups.')
print('PASS:',check_failure(run,exe,'cc','node','wasm-tools',p),'failed constructor image groups.')

print('PASS:',check_target_failure(run,exe,'cc','node','wasm-tools',p),'invalid target groups.')
