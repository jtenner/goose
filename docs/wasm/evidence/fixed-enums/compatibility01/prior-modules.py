from pathlib import Path
import subprocess,json,hashlib
r=Path('/home/dev/Projects/goose-wasm-backend');p=Path(__file__).parent;root=p.parent;rows=[]
sources=subprocess.check_output(['git','ls-tree','-r','--name-only','268b37b1a4203e8ebceb0f1c0e51321c3be91b4f','test/wasm'],cwd=r,text=True).splitlines()
sources += ['test/typing/'+n+'.goose' for n in ['global_optional_flow','optional_loop_callee_assignments','optional_while_condition_calls','u64_cmp_readonly_refs']]
for source in sources:
 if not source.endswith('.goose'):continue
 for opt in [0,2]:
  results=[]
  for label,exe in [('before',Path('/tmp/goose-wasm-fixed-struct-20261107/build04/goose-tested')),('after',root/'build02/goose-tested')]:
   stem=Path(source).stem+'-O'+str(opt)+'-'+label;w=p/(stem+'.wasm');a=subprocess.run([str(exe),'-O'+str(opt),'--target','wasm','-o',str(w),str(r/source)],cwd=r,capture_output=True,timeout=120)
   for ext,d in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]:
    with (p/(stem+'.'+ext)).open('xb') as f:f.write(d)
   assert not a.returncode,(stem,a.stderr);results.append((w.read_bytes(),a.stdout,a.stderr))
  row={'source':source,'opt':opt,'identical':results[0]==results[1],'before_bytes':len(results[0][0]),'after_bytes':len(results[1][0]),'before_sha256':hashlib.sha256(results[0][0]).hexdigest(),'after_sha256':hashlib.sha256(results[1][0]).hexdigest()};rows.append(row)
(p/'prior-module-summary.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps({'pairs':len(rows),'identical':sum(x['identical'] for x in rows),'changed':[x for x in rows if not x['identical']]},indent=2))
