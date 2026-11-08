from pathlib import Path
import subprocess,json,sys,hashlib
r=Path('/home/dev/Projects/goose-wasm-backend');p=Path(__file__).parent;exe=p.parent/'goose-tested';commands=[]
sys.path.insert(0,str(r/'test'))

def run(args,ok=True):
 args=list(map(str,args));name='command-'+str(len(commands));a=subprocess.run(args,cwd=r,capture_output=True,timeout=120)
 for ext,data in [('stdout',a.stdout),('stderr',a.stderr),('exit',(str(a.returncode)+'\n').encode())]:(p/(name+'.'+ext)).write_bytes(data)
 commands.append({'name':name,'args':args,'exit':a.returncode});(p/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
 if ok:assert not a.returncode,(name,args,a.stderr)
 return a
old=p.parent/'focused01'
old_rows=json.loads((old/'results.json').read_text());old_commands=json.loads((old/'commands.json').read_text());reuse=[]
for row in old_rows:
 source=r/row['source'];assert hashlib.sha256(source.read_bytes()).hexdigest()==row['source_sha256']
 module=old/(source.stem+f'-O{row["opt"]}.wasm')
 reuse.append(dict(row,module_sha256=hashlib.sha256(module.read_bytes()).hexdigest()))
(p/'reused.json').write_text(json.dumps(reuse,indent=2)+'\n')
rows=list(old_rows)
for source in sorted((r/'test/wasm').glob('wasm_fixed_argument_*.goose')):
 expected=(r/'test/expected'/(source.stem+'.out')).read_bytes()
 for opt in [0,2]:
  if any(x['source']==str(source.relative_to(r)) and x['opt']==opt for x in old_rows):continue
  module=p/(source.stem+f'-O{opt}.wasm')
  reused_hosts=source.stem=='wasm_fixed_argument_refs' and opt==0
  if reused_hosts:
   original=old/module.name
   prior=[x for x in old_commands if str(original) in x['args'] and 'wasm_multimemory.mjs' not in ' '.join(x['args'])]
   assert len(prior)==4 and all(x['exit']==0 for x in prior)
   import shutil
   shutil.copy2(original,module)
  else:run([exe,f'-O{opt}','--target','wasm','-o',module,source]);run(['wasm-tools','validate',module])
  for args in [['node',r/'test/wasm_reference_abi.mjs',module,p/(source.stem+f'-O{opt}-instance')],['/tmp/goose-wasm-runtime-env/bin/python',r/'test/wasmtime_host.py',module]]:
   if not reused_hosts:
    a=run(args);assert a.stdout==expected and not a.stderr,(source,opt,a)
  mode='' if source.stem.endswith(('_data_field','_refs','_reference_result')) else 'no-data'
  a=run(['node',r/'test/wasm_multimemory.mjs',module,'0',mode]);assert a.stdout==expected and not a.stderr
  rows.append({'source':str(source.relative_to(r)),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'opt':opt,'status':'PASS'});(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
print('PASS',len(rows),'argument case/optimization pairs in both hosts')
