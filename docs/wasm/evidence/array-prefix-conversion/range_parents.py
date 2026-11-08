from pathlib import Path
import subprocess,json,hashlib
p=Path(__file__).parent;q=p/'parent-ranges01';q.mkdir(exist_ok=True);r=Path('/home/dev/Projects/goose-wasm-backend');exe=Path('/tmp/goose-wasm-array-expression-source-20261108/build01/goose-tested');rows=[]
for name,sp,tp,n in [('u8','u16','u8',256),('u16','u32','u16',65536)]:
 f=q/(name+'.goose');f.write_text(f'fn main(){{var a:u8[{sp}]=[73;{n}];print("before");var b:u8[{tp}]=copy(a);print("after");}}\n');row={'case':name,'amount':n,'source_sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
 for kind,args in [('emit',[exe,'--standalone','-o',q/(name+'.c'),f]),('cc',['cc',q/(name+'.c'),'-pthread','-lm','-ldl','-o',q/(name+'.native')]),('native',[q/(name+'.native')]),('wasm',[exe,'-O0','--target','wasm','-o',q/(name+'.wasm'),f])]:
  args=list(map(str,args));a=subprocess.run(args,cwd=r,capture_output=True,timeout=120);row[kind+'_exit']=a.returncode
  (q/(name+'-'+kind+'.json')).write_text(json.dumps(args)+'\n')
  for k,v in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (q/(name+'-'+kind+'.'+k)).write_bytes(v)
  if kind in ['emit','cc']:assert a.returncode==0,a.stderr
  if kind=='native':assert a.returncode!=0 and a.stdout==b'before\n' and b'array length exceeds storage range' in a.stderr,a.stderr
  if kind=='wasm':assert a.returncode==1 and b'pending destination lowering' in a.stderr
 rows.append(row)
(q/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print('PASS two exact native range failures and parent Wasm admission rejections')
