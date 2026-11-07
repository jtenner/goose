from pathlib import Path
import subprocess,json,hashlib,sys
r=Path('/home/dev/Projects/goose-wasm-backend');p=Path(__file__).parent;exe=p.parent/'goose-tested';commands=[];rows=[];old=[]
sys.path.insert(0,str(r/'test'));from wasm_aggregate_construction_checks import check_modules
for folder in ['parent-first','parent-extra','parent-observers']:old+=json.loads((p.parent/folder/'results.json').read_text())
def run(args,ok=True):
 a=subprocess.run(list(map(str,args)),cwd=r,capture_output=True,timeout=120);stem=p/f'command{len(commands):04}'
 for ext,data in [('stdout',a.stdout),('stderr',a.stderr),('exit',(str(a.returncode)+'\n').encode())]:stem.with_suffix('.'+ext).write_bytes(data)
 commands.append({'args':list(map(str,args)),'exit':a.returncode});(p/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
 if ok:assert not a.returncode,(args,a.stdout,a.stderr)
 return a
print('PASS:',check_modules(run,'node','wasm-tools',p),'live-owner/complete-image/control groups.')
