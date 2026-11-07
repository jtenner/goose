from pathlib import Path
import subprocess,json,hashlib
p=Path(__file__).parent;root=p.parent;r=Path('/home/dev/Projects/goose-wasm-backend');rows=[]
sources=subprocess.check_output(['git','ls-tree','-r','--name-only','fcaba2e02bc6925f8e9c8c759f82d6eced526d21','test/wasm'],cwd=r,text=True).splitlines()
sources += ['test/typing/'+name+'.goose' for name in ['global_optional_flow','optional_loop_callee_assignments','optional_while_condition_calls','u64_cmp_readonly_refs']]
for source in sources:
 if not source.endswith('.goose'):continue
 for opt in [0,2]:
  results=[]
  for label,exe in [('before',Path('/tmp/goose-wasm-fixed-aggregate-arrays-20261107/build02/goose-tested')),('after',root/'build01/goose-tested')]:
   name=Path(source).stem+'-O'+str(opt)+'-'+label;w=p/(name+'.wasm');command=[str(exe),'-O'+str(opt),'--target','wasm','-o',str(w),str(r/source)];a=subprocess.run(command,cwd=r,capture_output=True,timeout=120)
   for ext,d in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]:
    with (p/(name+'.'+ext)).open('xb') as f:f.write(d)
   assert not a.returncode,(name,a.stderr);results.append((w.read_bytes(),a.stdout,a.stderr))
  assert results[0]==results[1],(source,opt,'accepted module changed')
  rows.append({'source':source,'opt':opt,'bytes':len(results[0][0]),'sha256':hashlib.sha256(results[0][0]).hexdigest()})
(p/'prior-modules.json').write_text(json.dumps(rows,indent=2)+'\n');print(str(len(rows))+' accepted module pairs byte-identical')
