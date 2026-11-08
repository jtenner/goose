from pathlib import Path
import subprocess,json,hashlib
p=Path(__file__).parent;q=p/'parent06';q.mkdir(exist_ok=True);r=Path('/home/dev/Projects/goose-wasm-backend');exe=Path('/tmp/goose-wasm-array-expression-source-20261108/build01/goose-tested');cases={
'owner_width':'fn main(){var a:i64[u8]=[7,-8,900];print("before");var b:i64[u16]=copy(a);print("after");assert(b.len==3&&b[0]==7&&b[1]== -8&&b[2]==900&&a.len==3&&a[0]==7);}\n',
'owner_leb_source':'fn main(){var a:u8[varint]=[73;128];print("before");var b:u8[u16]=copy(a);print("after");assert(b.len==128&&b[127]==73&&a.len==128&&a[127]==73);}\n',
'owner_leb_target':'fn main(){var a:u8[u16]=[73;128];print("before");var b:u8[varint]=copy(a);print("after");assert(b.len==128&&b[127]==73&&a.len==128&&a[127]==73);}\n',
'owner_empty':'fn main(){var a:u8[varint]=[];print("before");var b:u8[u16]=copy(a);print("after");assert(b.len==0&&a.len==0);}\n',
}
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
