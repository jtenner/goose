from pathlib import Path
import subprocess,json,hashlib
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');exe=Path('/tmp/goose-wasm-aggregate-prefix-20261108/build02/goose-tested');rows=[]
for name,source,target in [('grow_variable','[>..]','[u8]'),('grow_runtime','[>..]','[..]'),('runtime_variable','[..]','[u8]'),('runtime_grow','[..]','[>..]')]:
 f=p/(name+'.goose');f.write_text(f'fn main(){{var a:i64{source}=[7,-8];var b:i64{target}=copy(a);assert(b.len==2&&b[0]==7&&b[1]== -8);b[0]=31;assert(a[0]==7);print("{name}");}}\n')
 row={'case':name,'source_sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
 for kind,args in [('emit',[exe,'-O0','--standalone','-o',p/(name+'.c'),f]),('cc',['cc',p/(name+'.c'),'-pthread','-lm','-ldl','-o',p/(name+'.native')]),('native',[p/(name+'.native')]),('wasm',[exe,'-O0','--target','wasm','-o',p/(name+'.wasm'),f])]:
  args=list(map(str,args));a=subprocess.run(args,cwd=r,capture_output=True,timeout=120);row[kind+'_exit']=a.returncode
  (p/(name+'-'+kind+'.json')).write_text(json.dumps(args)+'\n')
  for k,v in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (p/(name+'-'+kind+'.'+k)).write_bytes(v)
  if kind!='wasm':assert a.returncode==0,(name,kind,a.stderr)
  else:assert a.returncode==1 and b'array adaptation needs the pending destination lowering' in a.stderr,(name,a.returncode,a.stderr)
 rows.append(row)
(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
(p.parent/'parent-compiler-identity.json').write_text(json.dumps({'compiler':str(exe),'sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'source_hashes':'/tmp/goose-wasm-aggregate-prefix-20261108/build02/source-hashes.json','parent_commit_pending_current_increment':True},indent=2)+'\n')
print('PASS 4 native-valid nonfixed-source failures')
