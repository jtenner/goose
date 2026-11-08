from pathlib import Path
import subprocess,json,hashlib
r=Path('/home/dev/Projects/goose-wasm-backend');base=Path('/tmp/goose-wasm-default-adaptation-20261108');p=Path(__file__).parent
exe=Path('/tmp/goose-wasm-array-assignment-20261107/build02/goose-tested');rows=[];commands=[]
def run(name,args):
 a=subprocess.run(list(map(str,args)),cwd=r,capture_output=True,timeout=120)
 for ext,data in [('stdout',a.stdout),('stderr',a.stderr),('exit',(str(a.returncode)+'\n').encode())]:(p/(name+'.'+ext)).write_bytes(data)
 commands.append({'name':name,'args':list(map(str,args)),'exit':a.returncode});(p/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
 assert not a.returncode,(name,a.stderr)
 return a
for group in ['reproduce01','parent-extra']:
 for source in sorted((base/group).glob('*.goose')):
  name=source.stem;expected=b'2\n' if group=='reproduce01' else (name+'\n').encode()
  for opt in [0,2]:
   stem=group+'-'+name+f'-O{opt}';module=p/(stem+'.wasm')
   run(stem+'-emit',[exe,f'-O{opt}','--target','wasm','-o',module,source]);run(stem+'-validate',['wasm-tools','validate',module])
   for host,args in [('node',['node',r/'scripts/run_wasm.mjs',module]),('wasmtime',['/tmp/goose-wasm-runtime-env/bin/python',r/'test/wasmtime_host.py',module])]:
    a=run(stem+'-'+host,args);assert a.stdout==expected and not a.stderr,(stem,host,a)
   rows.append({'case':group+'/'+name,'opt':opt,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'hosts':['Node','Wasmtime'],'status':'PASS'});(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
print('PASS',len(rows),'converted-default cases in both hosts')
