from pathlib import Path
import json,subprocess,hashlib
r=Path('/home/dev/Projects/goose-wasm-backend');p=Path('/tmp/goose-wasm-fixed-array-assignment-layout-20261108');p.mkdir(exist_ok=True);q=p/'parent01';q.mkdir(exist_ok=True)
exe=Path('/tmp/goose-wasm-fixed-result-layout-20261108/build01/goose-tested')
cases={
'stored':'fn main(){var a:i64[2]=[7,-8];var c:i64[..3]=[1,2,3];c=a;assert(c.len==2&&c[0]==7&&c[1] == -8);c.push(99);assert(c[2]==99&&a[0]==7);print("stored");}',
'call':'recursive fn make()->i64[2]{return[7,-8];}fn main(){var c:i64[..3]=[1,2,3];c=make();assert(c.len==2&&c[0]==7&&c[1] == -8);print("call");}',
'reference':'var calls:i64=0;recursive fn source(a:i64[2]&)->i64[2]&{calls++;return a;}fn main(){var a:i64[2]=[7,-8];var c:i64[..3]=[1,2,3];c=source(a);assert(calls==1&&c.len==2&&c[0]==7&&c[1] == -8);print("reference");}',
'data_field':'struct H{values:i64[..3]}var calls:i64=0;recursive fn index()->i64{calls++;return 0;}fn main(){var a:i64[2]=[7,-8];var rows:H[]=[H{[1,2,3]}];rows[index()].values=a;assert(calls==1&&rows[0].values.len==2&&rows[0].values[1] == -8);print("data_field");}',
'zero':'var calls:i64=0;recursive fn make()->i64[0]{calls++;return[];}fn main(){var c:i64[..1]=[7];c=make();assert(calls==1&&c.len==0);c.push(9);assert(c[0]==9);print("zero");}',
}
rows=[]
for n,s in cases.items():
 f=q/(n+'.goose');f.write_text(s+'\n');row={'case':n,'source_sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
 for kind,args in [('emit',[exe,'-O0','--standalone','-o',q/(n+'.c'),f]),('cc',['cc',q/(n+'.c'),'-pthread','-lm','-ldl','-o',q/(n+'.native')]),('native',[q/(n+'.native')]),('wasm',[exe,'-O0','--target','wasm','-o',q/(n+'.wasm'),f])]:
  a=subprocess.run(list(map(str,args)),cwd=r,capture_output=True,timeout=120)
  for k,v in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (q/(n+'-'+kind+'.'+k)).write_bytes(v)
  (q/(n+'-'+kind+'.json')).write_text(json.dumps(list(map(str,args)))+'\n');row[kind+'_exit']=a.returncode
  if kind=='native' and not a.returncode:assert a.stdout==(n+'\n').encode()
  if a.returncode and kind!='wasm':row['invalid_reason']=a.stderr.decode();break
  if kind=='wasm':row['wasm_reason']=a.stderr.decode()
 rows.append(row)
(q/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
(p/'parent-compiler-identity.json').write_text(json.dumps({'compiler':str(exe),'sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'source_commit':'pending fixed-array-layout checkpoint'},indent=2)+'\n')
