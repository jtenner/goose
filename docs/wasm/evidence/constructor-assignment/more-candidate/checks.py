from pathlib import Path
import subprocess,json,hashlib
r=Path('/home/dev/Projects/goose-wasm-backend');p=Path(__file__).parent;exe=p.parent/'build04/goose-tested';old=json.loads((p.parent/'more-parent/results.json').read_text());commands=[];rows=[]
def run(args):
 a=subprocess.run(list(map(str,args)),cwd=r,capture_output=True,timeout=120);stem=p/f'command{len(commands):03}'
 for ext,data in [('stdout',a.stdout),('stderr',a.stderr),('exit',(str(a.returncode)+'\n').encode())]:stem.with_suffix('.'+ext).write_bytes(data)
 commands.append({'args':list(map(str,args)),'exit':a.returncode});(p/'commands.json').write_text(json.dumps(commands,indent=2)+'\n');assert not a.returncode,(args,a.stdout,a.stderr);return a
for row in old:
 name=row['case'];opt=row['opt'];source=p.parent/'more-parent'/(name+'.goose');assert hashlib.sha256(source.read_bytes()).hexdigest()==row['source_sha256'];module=p/(name+f'-O{opt}.wasm');run([exe,f'-O{opt}','--target','wasm','-o',module,source]);run(['wasm-tools','validate',module]);expected=b'nested-live\nnested-done\nnested_assignment\n' if name=='nested_assignment' else (name+'\n').encode()
 for command in [['node',r/'scripts/run_wasm.mjs',module],['/tmp/goose-wasm-runtime-env/bin/python',r/'test/wasmtime_host.py',module]]:
  a=run(command);assert a.stdout==expected and not a.stderr,(name,opt,a.stdout,a.stderr)
 rows.append({**row,'candidate_node':'PASS','candidate_wasmtime':'PASS'});(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
print('PASS:',len(rows),'new cases in both Wasm engines.')
