from pathlib import Path
import subprocess,json,hashlib
p=Path(__file__).parent;q=p/'parent07';q.mkdir(exist_ok=True);r=Path('/home/dev/Projects/goose-wasm-backend');exe=Path('/tmp/goose-wasm-array-expression-source-20261108/build01/goose-tested');cases={'owner_overflow':'fn main(){var a:i64[u64]=[7,-8,900];print("before");var b:i64[u32]=copy(a);print("after");assert(a.len==3&&b.len==3&&b[0]==7&&b[1]== -8&&b[2]==900);}\n'}
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
