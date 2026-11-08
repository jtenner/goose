from pathlib import Path
import subprocess,json,hashlib,shutil
p=Path(__file__).parent;q=p/'parent01';r=Path('/home/dev/Projects/goose-wasm-backend');exe=Path('/tmp/goose-wasm-array-expression-source-20261108/build01/goose-tested');cases={
 'widen':'fn main(){var a:u8[u8]=[1,2,3];var b:u8[u16]=copy(a);assert(b.len==3&&b[0]==1&&b[2]==3);print("widen");}\n',
 'reference':'fn main(){var a:u8[u8]=[1,2,3];var r:u8[u8]&=a;var b:u8[u16]=copy(r);assert(b.len==3&&b[0]==1&&b[2]==3);print("reference");}\n',
 'leb_source':'fn main(){var a:u8[varint]=[1,2,3];var b:u8[u16]=copy(a);assert(b.len==3&&b[0]==1&&b[2]==3);print("leb_source");}\n',
 'leb_target':'fn main(){var a:u8[u16]=[1,2,3];var b:u8[varint]=copy(a);assert(b.len==3&&b[0]==1&&b[2]==3);print("leb_target");}\n',
 'data_reference_field':'struct H{r:u8[u8]&}fn main(){var a:u8[u8]=[1,2,3];var rows:H[]=[H{a}];var b:u8[u16]=copy(rows[0].r);assert(b.len==3&&b[0]==1&&b[2]==3);print("data_reference_field");}\n',
}
rows=[]
for name,text in cases.items():
 f=q/(name+'.goose');f.write_text(text);row={'case':name,'source_sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
 for kind,args in [('emit',[exe,'--standalone','-o',q/(name+'.c'),f]),('cc',['cc',q/(name+'.c'),'-pthread','-lm','-ldl','-o',q/(name+'.native')]),('native',[q/(name+'.native')]),('wasm',[exe,'-O0','--target','wasm','-o',q/(name+'.wasm'),f])]:
  args=list(map(str,args));a=subprocess.run(args,cwd=r,capture_output=True,timeout=120);row[kind+'_exit']=a.returncode
  (q/(name+'-'+kind+'.json')).write_text(json.dumps(args)+'\n')
  for k,v in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (q/(name+'-'+kind+'.'+k)).write_bytes(v)
  if a.returncode and kind!='wasm':break
 rows.append(row)
(q/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
(p/'parent-compiler-identity.json').write_text(json.dumps({'compiler':str(exe),'sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'source_stage':'/tmp/goose-wasm-array-expression-source-20261108'},indent=2)+'\n')
shutil.copy2('/tmp/goose-wasm-array-expression-source-20261108/run_suite.py',p/'run_suite.py')
