from pathlib import Path
import subprocess,json,hashlib,sys
r=Path('/home/dev/Projects/goose-wasm-backend');p=Path(__file__).parent;exe=p.parent/'goose-tested';commands=[];rows=[];old=[]
sys.path.insert(0,str(r/'test'));from wasm_array_assignment_checks import check_images,check_references,check_guards
for folder in ['parent-first','parent-extra','parent-image','parent-index','parent-field']:old+=json.loads((p.parent/folder/'results.json').read_text())
def run(args,ok=True):
 a=subprocess.run(list(map(str,args)),cwd=r,capture_output=True,timeout=120);stem=p/f'command{len(commands):04}'
 for ext,data in [('stdout',a.stdout),('stderr',a.stderr),('exit',(str(a.returncode)+'\n').encode())]:stem.with_suffix('.'+ext).write_bytes(data)
 commands.append({'args':list(map(str,args)),'exit':a.returncode});(p/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
 if ok:assert not a.returncode,(args,a.stdout,a.stderr)
 return a
for source in sorted((r/'test/wasm').glob('wasm_array_assignment_*.goose')):
 name=source.stem.removeprefix('wasm_array_assignment_');expected=(r/'test/expected'/(source.stem+'.out')).read_bytes()
 for opt in [0,2]:
  parent=[x for x in old if x['case']==name and x['opt']==opt];assert len(parent)==1;assert parent[0]['source_sha256']==hashlib.sha256(source.read_bytes()).hexdigest();module=p/(source.stem+f'-O{opt}.wasm');run([exe,f'-O{opt}','--target','wasm','-o',module,source]);run(['wasm-tools','validate',module])
  for command in [['node',r/'scripts/run_wasm.mjs',module],['/tmp/goose-wasm-runtime-env/bin/python',r/'test/wasmtime_host.py',module]]:
   a=run(command);assert a.stdout==expected and not a.stderr,(name,opt,a.stdout,a.stderr)
  rows.append({**parent[0],'candidate_node':'PASS','candidate_wasmtime':'PASS'});(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
print('PASS:',len(rows),'both-engine exact-array cases.')
print('PASS:',check_images(run,'node','wasm-tools',p),'complete-image/control groups.')
print('PASS:',check_references(run,'node','wasm-tools',Path('/tmp/goose-wasm-runtime-env/bin/python'),p),'opaque-reference guard groups.')
print('PASS:',check_guards(run,exe,'cc','node',p),'native-valid retained guard groups.')
