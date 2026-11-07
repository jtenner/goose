from pathlib import Path
import json,subprocess,runpy,hashlib
r=Path('/home/dev/Projects/goose-wasm-backend');p=Path(__file__).parent;before=p.parent/'review-repair/reproduce02';spec=runpy.run_path(str(r/'test/wasm_array_copy_admission.py'));rows=[]
for name,source in spec['CASES'].items():
 s=before/(name+'.goose');assert s.read_text()==source+'\n'
 for opt in [0,2]:
  n=name+'-O'+str(opt);w=p/(n+'-rejected.wasm');w.unlink(missing_ok=True)
  command=[str(r/'build/goose'),'-O'+str(opt),'--target','wasm','-o',str(w),str(s)]
  a=subprocess.run(command,cwd=r,capture_output=True,timeout=90)
  for ext,data in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (p/(n+'-admission.'+ext)).write_bytes(data)
  assert a.returncode and spec['reason'](name) in a.stderr and not w.exists(),(name,opt,a.returncode,a.stderr)
  rows.append({'case':name,'opt':opt,'source_sha256':hashlib.sha256(s.read_bytes()).hexdigest(),'command':command,'exit':a.returncode,'no_module':not w.exists(),'expected_reason':spec['reason'](name).decode()})
(p/'admission-results.json').write_text(json.dumps(rows,indent=2)+'\n');print(str(len(rows))+' exact-reason admission checks passed')
