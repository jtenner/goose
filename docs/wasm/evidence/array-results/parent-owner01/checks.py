from pathlib import Path
import subprocess,json,hashlib,shutil
r=Path('/home/dev/Projects/goose-wasm-backend');p=Path(__file__).parent;exe=Path('/tmp/goose-wasm-array-arguments-20261108/build01/goose-tested');commands=[]
source=p/'owner.goose'
expected=b'before\narg-live\ncallee-live\ndefer\nafter\n'
def run(name,args):
 args=list(map(str,args));a=subprocess.run(args,cwd=r,capture_output=True,timeout=120)
 for ext,data in [('stdout',a.stdout),('stderr',a.stderr),('exit',(str(a.returncode)+'\n').encode())]:(p/(name+'.'+ext)).write_bytes(data)
 commands.append({'name':name,'args':args,'exit':a.returncode});(p/'commands.json').write_text(json.dumps(commands,indent=2)+'\n');return a
rows=[]
for opt in [0,2]:
 c=p/f'owner-O{opt}.c';native=c.with_suffix('.native');module=c.with_suffix('.wasm')
 for label,args in [('emit',[exe,f'-O{opt}','--standalone','-o',c,source]),('cc',['cc',c,'-pthread','-lm','-ldl','-o',native]),('native',[native])]:
  a=run(f'O{opt}-'+label,args);assert not a.returncode,(label,a.stderr)
  if label=='native':assert a.stdout==expected and not a.stderr,a
 a=run(f'O{opt}-before',[exe,f'-O{opt}','--target','wasm','-o',module,source]);assert a.returncode==1 and b'array results need' in a.stderr and not module.exists()
 rows.append({'opt':opt,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'native':'PASS','wasm':'expected guard'})
(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print('PASS',len(rows),'native-first owner cases')
