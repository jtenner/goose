from pathlib import Path
import subprocess,json,sys
p=Path(__file__).parent;root=p.parent;r=Path('/home/dev/Projects/goose-wasm-backend');exe=root/'build02/goose-tested';native=root/'build01/goose-tested';rows=[];failed=[]
def run(name,args):
 args=list(map(str,args));a=subprocess.run(args,cwd=r,capture_output=True,timeout=180)
 for ext,d in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]:
  with (p/(name+'.'+ext)).open('xb') as f:f.write(d)
 rows.append({'name':name,'command':args,'exit':a.returncode});(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n');return a
for name,(text,reason) in json.loads((root/'admission-cases.json').read_text()).items():
 source=p/(name+'.goose');source.write_text(text)
 for opt in [0,2]:
  stem=name+'-O'+str(opt);c=p/(stem+'.c');a=run(stem+'-native-emit',[native,'-O'+str(opt),'--standalone','-o',c,source])
  if a.returncode:failed.append(stem+' native invalid');continue
  binary=p/(stem+'.native');a=run(stem+'-native-build',['cc','-O0',c,'-pthread','-lm','-ldl','-o',binary])
  if a.returncode:failed.append(stem+' native build');continue
  a=run(stem+'-native-run',[binary])
  if a.returncode:failed.append(stem+' native run');continue
  w=p/(stem+'.wasm');a=run(stem+'-reject',[exe,'-O'+str(opt),'--target','wasm','-o',w,source])
  if not a.returncode or reason.encode() not in a.stderr or w.exists():failed.append(stem+' target admission')
for name in ['control','wildcard']:
 for opt in [0,2]:
  stem=name+'-O'+str(opt);source=root/(name+'.goose');c=p/(stem+'.c');binary=p/(stem+'.native');w=p/(stem+'.wasm')
  a=run(stem+'-native-emit',[native,'-O'+str(opt),'--standalone','-o',c,source]);assert not a.returncode
  a=run(stem+'-native-build',['cc','-O0',c,'-pthread','-lm','-ldl','-o',binary]);assert not a.returncode
  expected=run(stem+'-native-run',[binary]);assert not expected.returncode
  a=run(stem+'-emit',[exe,'-O'+str(opt),'--target','wasm','-o',w,source]);assert not a.returncode
  a=run(stem+'-validate',['wasm-tools','validate',w]);assert not a.returncode
  for runtime,cmd in [('node',['node',r/'scripts/run_wasm.mjs',w]),('wasmtime',['/tmp/goose-wasm-runtime-env/bin/python',r/'test/wasmtime_host.py',w])]:
   a=run(stem+'-'+runtime,cmd)
   if a.returncode or a.stdout!=expected.stdout or a.stderr:failed.append(stem+' '+runtime)
  a=run(stem+'-wat',['wasm-tools','print',w]);assert not a.returncode
for case in json.loads((root/'promoted.json').read_text()):
 for opt in [0,2]:
  name=case+'-O'+str(opt);w=root/'build02'/(name+'.wasm');expected=(r/'test/expected'/(case+'.out')).read_bytes()
  mode='frame-growth' if case=='wasm_enum_cleanup' else '' if case in ['wasm_enum_containers'] else 'no-data'
  a=run(name+'-owner',['node',r/'test/wasm_multimemory.mjs',w,'0',mode])
  if a.returncode or a.stdout!=expected or a.stderr:failed.append(name+' owner')
a=run('tags-wat',['wasm-tools','print',root/'build02/wasm_enum_tags-O0.wasm']);assert not a.returncode
(p/'summary.json').write_text(json.dumps({'failed':failed,'checks':len(rows)},indent=2)+'\n');print(json.dumps({'failed':failed,'checks':len(rows)}));sys.exit(bool(failed))
