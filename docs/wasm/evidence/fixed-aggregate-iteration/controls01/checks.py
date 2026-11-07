from pathlib import Path
import json,hashlib,subprocess,sys
p=Path(__file__).parent;root=p.parent;r=Path('/home/dev/Projects/goose-wasm-backend');exe=root/'build01/goose-tested';rows=[];failed=[]
assert hashlib.sha256(exe.read_bytes()).hexdigest()=='c9519e59d47ea996b84d249fee688704bfab0ed49cf5c1ef844e7daf3bdd60d2'
for n,h in json.loads((root/'build01/source-hashes.json').read_text()).items():assert hashlib.sha256((r/n).read_bytes()).hexdigest()==h,n

def run(name,args):
 args=list(map(str,args));a=subprocess.run(args,cwd=r,capture_output=True,timeout=120)
 for ext,value in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]:
  with (p/(name+'.'+ext)).open('xb') as f:f.write(value)
 rows.append({'name':name,'command':args,'exit':a.returncode});(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n');return a
for name in ['control','checkpoint','zero_control','frame_limit']:
 source=p/(name+'.goose');source.write_bytes((root/(name+'.goose')).read_bytes())
 for opt in [0,2]:
  stem=name+'-O'+str(opt);c=p/(stem+'.c');native=p/(stem+'.native');w=p/(stem+'.wasm')
  a=run(stem+'-native-emit',[exe,'-O'+str(opt),'--standalone','-o',c,source])
  if a.returncode:failed.append(stem+' native source');continue
  if name!='frame_limit':
   a=run(stem+'-native-build',['cc','-O0',c,'-pthread','-lm','-ldl','-o',native])
   if a.returncode:failed.append(stem+' native build');continue
   a=run(stem+'-native-run',[native]);expected=a.stdout
   if a.returncode or a.stderr:failed.append(stem+' native run');continue
  a=run(stem+'-emit',[exe,'-O'+str(opt),'--target','wasm','-o',w,source])
  if name=='frame_limit':
   if not a.returncode or b'frame exceeds memory32' not in a.stderr or w.exists():failed.append(stem+' wrong frame gate')
   continue
  if a.returncode:failed.append(stem+' emit');continue
  a=run(stem+'-validate',['wasm-tools','validate',w])
  if a.returncode:failed.append(stem+' validate');continue
  text=run(stem+'-dump',['wasm-tools','print',w]).stdout.decode();(p/(stem+'.wat')).write_text(text)
  for engine,args in [('node',['node',r/'scripts/run_wasm.mjs',w]),('wasmtime',['/tmp/goose-wasm-runtime-env/bin/python',r/'test/wasmtime_host.py',w])]:
   a=run(stem+'-'+engine,args)
   if a.returncode or a.stderr or a.stdout!=expected:failed.append(stem+' '+engine)
  mode={'control':'copy','checkpoint':'cleanup','zero_control':'zero'}[name];memories=3 if name=='checkpoint' else 1
  assert 'test_stack_top_0' not in text
  exports=''.join(f'  (export "test_stack_top_{i}" (global {i}))\n' for i in range(memories))
  derived=p/(stem+'-owner.wat');derived.write_text(text[:text.rfind(')')]+exports+')\n');module=derived.with_suffix('.wasm')
  a=run(stem+'-owner-parse',['wasm-tools','parse',derived,'-o',module]);b=run(stem+'-owner-validate',['wasm-tools','validate',module])
  if a.returncode or b.returncode:failed.append(stem+' owner module');continue
  a=run(stem+'-live-owner',['node',r/'test/wasm_iteration_owner.mjs',module,mode])
  if a.returncode or a.stderr or a.stdout!=expected:failed.append(stem+' live owner')
(p/'summary.json').write_text(json.dumps({'failed':failed,'commands':len(rows)},indent=2)+'\n');print(json.dumps({'failed':failed,'commands':len(rows)}));sys.exit(bool(failed))
