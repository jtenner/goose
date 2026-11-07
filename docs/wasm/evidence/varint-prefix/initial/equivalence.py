from pathlib import Path
import subprocess,json,hashlib
r=Path('/home/dev/Projects/goose-wasm-backend');p=Path('/tmp/goose-wasm-varint-prefix-20261107/equivalence');p.mkdir(exist_ok=True);rows=[]
sources=subprocess.check_output(['git','ls-tree','-r','--name-only','HEAD','test/wasm'],cwd=r,text=True).splitlines()
for source in sources:
 if not source.endswith('.goose'):continue
 for opt in [0,2]:
  outputs=[]
  for label,compiler in [('before','/tmp/goose-wasm-array-copy-20261107/final-validation/goose-tested'),('after',str(r/'build/goose'))]:
   name=Path(source).stem+'-O'+str(opt)+'-'+label;w=p/(name+'.wasm');a=subprocess.run([compiler,'-O'+str(opt),'--target','wasm','-o',str(w),str(r/source)],cwd=r,capture_output=True)
   for ext,value in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (p/(name+'.'+ext)).write_bytes(value)
   assert not a.returncode,(name,a.stderr);outputs.append((w.read_bytes(),a.stdout,a.stderr))
  assert outputs[0]==outputs[1],(source,opt,'previous Wasm output changed')
  rows.append({'source':source,'opt':opt,'bytes':len(outputs[0][0]),'sha256':hashlib.sha256(outputs[0][0]).hexdigest()})
(p/'summary.json').write_text(json.dumps(rows,indent=2)+'\n');print(str(len(rows))+' prior modules unchanged')
