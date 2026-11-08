from pathlib import Path
import subprocess,json
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');exe=Path('/tmp/goose-wasm-fixed-negation-20261108/build01/goose-tested');rows=[]
for name in ['fixed_math_destinations','fixed_math_lifetimes','fixed_math_capacity']:
 f=r/'test/codegen'/(name+'.goose');c=p/(name+'.c');out=p/(name+'.native');row={'name':name}
 for phase,args in [('emit',[exe,'-O0','--standalone','-o',c,f]),('cc',['cc',c,'-pthread','-lm','-ldl','-o',out]),('run',[out])]:
  a=subprocess.run(list(map(str,args)),cwd=r,capture_output=True,timeout=120)
  for k,v in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (p/(name+'-'+phase+'.'+k)).write_bytes(v)
  row[phase]=a.returncode
  if a.returncode: break
 rows.append(row)
(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print(rows)
