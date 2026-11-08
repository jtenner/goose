from pathlib import Path
import json,hashlib,subprocess
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');exe=p.parent/'build01/goose-tested';rows=[]
for row in json.loads((p.parent/'parent05-audit/results.json').read_text()):
 if row['scope']!='separate existing guard':continue
 f=Path(row['source']);assert hashlib.sha256(f.read_bytes()).hexdigest()==row['source_sha256']
 for opt in [0,2]:
  name=row['case']+f'-O{opt}';module=p/(name+'.wasm');a=subprocess.run([str(exe),f'-O{opt}','--target','wasm','-o',str(module),str(f)],cwd=r,capture_output=True,timeout=120)
  for k,v in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (p/(name+'.'+k)).write_bytes(v)
  assert a.returncode==1 and row['wasm_expected'].encode() in a.stderr and not module.exists(),(row,a)
  rows.append({'case':row['case'],'opt':opt,'reason':row['wasm_expected'],'status':'PASS'})
(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n');assert len(rows)==6;print('PASS6 specific inherited layout/call guards,no partial module')
