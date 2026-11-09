from pathlib import Path
import subprocess,json,hashlib
p=Path(__file__).parent;q=p/'parent03';q.mkdir(exist_ok=True);r=Path('/home/dev/Projects/goose-wasm-backend');exe=Path('/tmp/goose-wasm-array-prefix-conversion-20261108/build01/goose-tested');cases={}
for prefix in ['u8','u16','u64']:
 cases[prefix+'_variant']='enum E{A{n:i64,cells:u16[2]},B}'+f'fn main(){{var a:E.A[{prefix}]=[E.A{{7,[100,200]}},E.A{{8,[300,400]}}];var b:E.A[{prefix}]=copy(a);b[0].cells[1]=31;var total:i64=0;for v,i in a{{assert(&v .!= &a[i]);total+=v.n;}}assert(total==15&&a[0].cells[1]==200&&b[0].cells[1]==31&&b[1].n==8);print("{prefix}_variant");}}\n'

rows=[]
for name,source in cases.items():
 f=q/(name+'.goose');f.write_text(source);row={'case':name,'source_sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
 for kind,args in [('emit',[exe,'--standalone','-o',q/(name+'.c'),f]),('cc',['cc',q/(name+'.c'),'-pthread','-lm','-ldl','-o',q/(name+'.native')]),('native',[q/(name+'.native')]),('wasm',[exe,'-O0','--target','wasm','-o',q/(name+'.wasm'),f])]:
  args=list(map(str,args));a=subprocess.run(args,cwd=r,capture_output=True,timeout=120);row[kind+'_exit']=a.returncode
  (q/(name+'-'+kind+'.json')).write_text(json.dumps(args)+'\n')
  for k,v in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (q/(name+'-'+kind+'.'+k)).write_bytes(v)
  if a.returncode and kind!='wasm':break
 rows.append(row)
(q/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
