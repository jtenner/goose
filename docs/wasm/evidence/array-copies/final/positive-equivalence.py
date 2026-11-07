from pathlib import Path
import subprocess,json,hashlib
r=Path('/home/dev/Projects/goose-wasm-backend');p=Path(__file__).parent;rows=[]
for name in ['values','inline','cleanup','sources']:
 for opt in [0,2]:
  w=p/(name+'-O'+str(opt)+'-before-guard.wasm');command=[str(p.parent/'goose-tested'),'-O'+str(opt),'--target','wasm','-o',str(w),str(p/(name+'.goose'))]
  a=subprocess.run(command,cwd=r,capture_output=True,timeout=90)
  for ext,data in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (p/(name+'-O'+str(opt)+'-before-guard.'+ext)).write_bytes(data)
  assert a.returncode==0,(name,opt,a.stderr)
  after=p/(name+'-O'+str(opt)+'.wasm');assert w.read_bytes()==after.read_bytes(),(name,opt,'guard changed accepted copy module')
  rows.append({'case':name,'opt':opt,'bytes':w.stat().st_size,'sha256':hashlib.sha256(w.read_bytes()).hexdigest()})
(p/'positive-equivalence.json').write_text(json.dumps(rows,indent=2)+'\n');print(str(len(rows))+' accepted copy modules unchanged by guards')
