from pathlib import Path
import subprocess,json,hashlib
r=Path('/home/dev/Projects/goose-wasm-backend');root=Path('/tmp/goose-wasm-constructor-assignment-20261107');p=Path(__file__).parent;exe=root/'build01/goose-tested';rows=[];commands=[]
def run(name,args):
 a=subprocess.run([str(x) for x in args],cwd=r,capture_output=True,timeout=120)
 for ext,data in [('stdout',a.stdout),('stderr',a.stderr),('exit',(str(a.returncode)+'\n').encode())]:
  dest=p/(name+'.'+ext);assert not dest.exists();dest.write_bytes(data)
 commands.append({'name':name,'args':[str(x) for x in args],'exit':a.returncode});(p/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
 assert a.returncode==0,(name,a.returncode,a.stdout,a.stderr)
 return a
old=json.loads((root/'parent-first/results.json').read_text());extra=json.loads((root/'parent-extra02/results.json').read_text())
for name in ['default','alias','refs','nested','early','growth','loop','global','empty','variant-empty']:
 source=root/('parent-extra02' if name=='variant-empty' else 'parent-first')/(name+'.goose')
 previous=[x for x in old+extra if x['case']==name];assert len(previous)==2
 assert all(x['source_sha256']==hashlib.sha256(source.read_bytes()).hexdigest() for x in previous)
 expected=(b'inner\nouter\ninner\nouter\nearly\n' if name=='early' else b'step\n'*4+b'loop\n' if name=='loop' else (name+'\n').encode())
 for opt in [0,2]:
  stem=name+f'-O{opt}';module=p/(stem+'.wasm')
  run(stem+'-emit',[exe,f'-O{opt}','--target','wasm','-o',module,source])
  run(stem+'-validate',['wasm-tools','validate',module])
  for engine,args in [('node',['node',r/'scripts/run_wasm.mjs',module]),('wasmtime',['/tmp/goose-wasm-runtime-env/bin/python',r/'test/wasmtime_host.py',module])]:
   a=run(stem+'-'+engine,args);assert a.stdout==expected and not a.stderr,(stem,engine,a.stdout,a.stderr)
  rows.append({'case':name,'opt':opt,'native_reused':previous,'node':'PASS','wasmtime':'PASS'});(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
print('PASS:20 constructor cases, both Wasm engines, native outputs reused by source hash.')
