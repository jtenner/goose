from pathlib import Path
import subprocess,json,hashlib
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');parent=Path('/tmp/goose-wasm-array-prefix-conversion-20261108/build01/goose-tested');cases={
 'frame':'fn main(){var a:u16[..3]=[1,2,3];var r:u16& =a[2];for i in 2{if i==0{a=[1,2,3];}else{a=[4];}}print("slot=",r);assert(r==0);}\n',
 'stored_copy':'struct S{xs:u16[..3]}fn main(){var source=S{[1,2,3]};var sr:u16& =source.xs[2];source.xs.pop();sr=99;var a:S[]=[S{[1,2,3]}];var r:u16& =a[0].xs[2];a[0]=copy(source);print("slot=",r);assert(r==99&&a[0].xs.len==2);}\n',
};rows=[]
for name,text in cases.items():
 f=p/(name+'.goose');f.write_text(text);row={'case':name,'source_sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
 for phase,args in [('emit',[parent,'--standalone','-o',p/(name+'.c'),f]),('cc',['cc',p/(name+'.c'),'-pthread','-lm','-ldl','-o',p/(name+'.native')]),('native',[p/(name+'.native')]),('wasm',[parent,'-O0','--target','wasm','-o',p/(name+'.wasm'),f]),('validate',['wasm-tools','validate',p/(name+'.wasm')]),('node',['node',r/'scripts/run_wasm.mjs',p/(name+'.wasm')])]:
  args=list(map(str,args));a=subprocess.run(args,cwd=r,capture_output=True,timeout=120);row[phase+'_exit']=a.returncode
  (p/(name+'-'+phase+'.json')).write_text(json.dumps(args)+'\n')
  for k,v in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (p/(name+'-'+phase+'.'+k)).write_bytes(v)
  if phase in ['native','node']:row[phase+'_stdout']=a.stdout.decode();row[phase+'_stderr']=a.stderr.decode()
  if a.returncode and phase not in ['native','node']:break
 rows.append(row)
(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
