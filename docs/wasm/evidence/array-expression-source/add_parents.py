from pathlib import Path
import subprocess,json,hashlib
p=Path(__file__).parent;q=p/'parent02';q.mkdir(exist_ok=True);r=Path('/home/dev/Projects/goose-wasm-backend');exe='/tmp/goose-wasm-limited-array-conversion-20261108/build02/goose-tested'
cases={}
for kind,shape in [('fixed','[2]'),('limited','[..3]')]:
 t='u8'+shape
 cases[kind+'_reference_binding']=f'var source:{t}=[7,8];fn main(){{var r:{t}& =({{defer source[0]=99;source}});var b:u8[]=copy(r);assert(b.len==2&&b[0]==99&&source[0]==99);print("reference_binding");}}\n'
 cases[kind+'_global']=f'var result:u8[]=({{var a:{t}=[7,8];a}});fn main(){{assert(result.len==2&&result[1]==8);print("global");}}\n'
cases.update({
 'fixed_grow':'fn main(){var b:u8[>..]=({var a:u8[2]=[7,8];a});b.push(9);assert(b.len==3&&b[2]==9);print("fixed_grow");}\n',
 'limited_runtime':'fn main(){var b:u8[..]=({var a:u8[..3]=[7,8];a});assert(b.len==2&&b.cap==2&&b[1]==8);print("limited_runtime");}\n',
 'fixed_varint':'fn main(){var b:u8[varint]=({var a:u8[2]=[7,8];a});assert(b.len==2&&b[1]==8);print("fixed_varint");}\n',
 'limited_varint':'fn main(){var b:u8[varint]=({var a:u8[..3]=[7,8];a});assert(b.len==2&&b[1]==8);print("limited_varint");}\n',
})
rows=[]
for name,source in cases.items():
 f=q/(name+'.goose');f.write_text(source);row={'case':name,'source_sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
 for kind,args in [('emit',[exe,'--standalone','-o',q/(name+'.c'),f]),('cc',['cc',q/(name+'.c'),'-pthread','-lm','-ldl','-o',q/(name+'.native')]),('native',[q/(name+'.native')]),('wasm',[exe,'-O0','--target','wasm','-o',q/(name+'.wasm'),f])]:
  args=list(map(str,args));a=subprocess.run(args,cwd=r,capture_output=True,timeout=120);row[kind+'_exit']=a.returncode
  for k,v in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (q/(name+'-'+kind+'.'+k)).write_bytes(v)
  (q/(name+'-'+kind+'.json')).write_text(json.dumps(args)+'\n')
  if a.returncode and kind!='wasm':break
 rows.append(row)
(q/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print(rows)
