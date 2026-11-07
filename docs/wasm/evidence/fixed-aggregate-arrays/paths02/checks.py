from pathlib import Path
import subprocess,json,sys,hashlib
p=Path(__file__).parent;root=p.parent;r=Path('/home/dev/Projects/goose-wasm-backend');native=Path('/tmp/goose-wasm-fixed-enum-20261107/build02/goose-tested');exe=root/'build02/goose-tested';rows=[];failed=[]
assert hashlib.sha256(exe.read_bytes()).hexdigest()=='bd3856b6c2eedd69bd4eaf343aa9f505794f1a17ab3383194b218fbe33fa368d'
def run(name,args):
 args=list(map(str,args));a=subprocess.run(args,cwd=r,capture_output=True,timeout=180)
 for ext,d in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]:
  with (p/(name+'.'+ext)).open('xb') as f:f.write(d)
 rows.append({'name':name,'command':args,'exit':a.returncode});(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n');return a
cases=json.loads((root/'additional-gates.json').read_text());cases['callbacks']=[(root/'callbacks.goose').read_text(),None]
for case,(text,reasons) in cases.items():
 source=p/(case+'.goose');source.write_text(text)
 for opt in [0,2]:
  name=case+'-O'+str(opt);c=p/(name+'.c');binary=p/(name+'.native');w=p/(name+'.wasm')
  a=run(name+'-native-emit',[native,'-O'+str(opt),'--standalone','-o',c,source])
  if a.returncode:failed.append(name+' native emit');continue
  a=run(name+'-native-build',['cc','-O0',c,'-pthread','-lm','-ldl','-o',binary])
  if a.returncode:failed.append(name+' native build');continue
  expected=run(name+'-native-run',[binary])
  if expected.returncode:failed.append(name+' native run');continue
  a=run(name+'-target',[exe,'-O'+str(opt),'--target','wasm','-o',w,source])
  if reasons:
   if not a.returncode or w.exists() or not any(reason.encode() in a.stderr for reason in reasons):failed.append(name+' target gate')
   continue
  if a.returncode:failed.append(name+' target emit');continue
  a=run(name+'-validate',['wasm-tools','validate',w])
  if a.returncode:failed.append(name+' validate');continue
  for runtime,command in [('node',['node',r/'scripts/run_wasm.mjs',w]),('wasmtime',['/tmp/goose-wasm-runtime-env/bin/python',r/'test/wasmtime_host.py',w]),('owner',['node',r/'test/wasm_multimemory.mjs',w,'0',''])]:
   a=run(name+'-'+runtime,command)
   if a.returncode or a.stdout!=expected.stdout or a.stderr:failed.append(name+' '+runtime)
(p/'summary.json').write_text(json.dumps({'failed':failed,'commands':len(rows)},indent=2)+'\n');print(json.dumps({'failed':failed,'commands':len(rows)}));sys.exit(bool(failed))
