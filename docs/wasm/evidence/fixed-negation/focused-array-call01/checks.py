from pathlib import Path
import subprocess,json,sys,hashlib
r=Path('/home/dev/Projects/goose-wasm-backend');p=Path(__file__).parent;exe=p.parent/'build01/goose-tested';commands=[]
sys.path.insert(0,str(r/'test'))
def run(args,ok=True):
 args=list(map(str,args));name='command-'+str(len(commands));a=subprocess.run(args,cwd=r,capture_output=True,timeout=180)
 for ext,data in [('stdout',a.stdout),('stderr',a.stderr),('exit',(str(a.returncode)+'\n').encode())]:(p/(name+'.'+ext)).write_bytes(data)
 commands.append({'name':name,'args':args,'exit':a.returncode});(p/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
 if ok:assert not a.returncode,(name,args,a.stderr)
 return a
rows=[]
for source in sorted((r/'test/wasm').glob('wasm_fixed_negation_array_call.goose')):
 expected=(r/'test/expected'/(source.stem+'.out')).read_bytes()
 for opt in [0,2]:
  module=p/(source.stem+f'-O{opt}.wasm');run([exe,f'-O{opt}','--target','wasm','-o',module,source]);run(['wasm-tools','validate',module])
  for args in [['node',r/'test/wasm_reference_abi.mjs',module,p/(source.stem+f'-O{opt}-instance')],['/tmp/goose-wasm-runtime-env/bin/python',r/'test/wasmtime_host.py',module]]:
   a=run(args);assert a.stdout==expected and not a.stderr,(source,opt,a)
  mode='no-data'
  a=run(['node',r/'test/wasm_multimemory.mjs',module,'0',mode]);assert a.stdout==expected and not a.stderr
  rows.append({'source':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'opt':opt,'status':'PASS'});(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
print('PASS',len(rows),'fixed negation pairs in both hosts')
