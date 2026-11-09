from pathlib import Path
import subprocess,json,hashlib
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');exe=Path('/tmp/goose-wasm-array-prefix-conversion-20261108/build01/goose-tested');cases={}
for name,prefix,amount in [('u8_255','u8',255),('u16_256','u16',256)]:
 cases[name]='struct Cell{n:u8}fn main(){var rows:Cell['+prefix+']=['+','.join(['Cell{1}']*amount)+f'];assert(rows.len=={amount}&&rows[{amount-1}].n==1);print("{name}");}}\n'
cases['guard_leb']='struct S{n:i64}fn main(){var rows:S[varint]=[S{7}];assert(rows[0].n==7);print("leb");}\n'
cases['guard_fill']='struct S{n:i64}fn main(){var rows:S[u8]=[S{7};2];assert(rows[1].n==7);print("fill");}\n'
cases['guard_zero']='struct S{}fn main(){var rows:S[u8]=[S{}];assert(rows.len==1);print("zero");}\n'
rows=[]
for name,text in cases.items():
 f=p/(name+'.goose');f.write_text(text);row={'case':name,'source_sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
 for phase,args in [('emit',[exe,'--standalone','-o',p/(name+'.c'),f]),('cc',['cc',p/(name+'.c'),'-pthread','-lm','-ldl','-o',p/(name+'.native')]),('native',[p/(name+'.native')]),('wasm',[exe,'-O0','--target','wasm','-o',p/(name+'.wasm'),f])]:
  args=list(map(str,args));a=subprocess.run(args,cwd=r,capture_output=True,timeout=120);row[phase+'_exit']=a.returncode
  (p/(name+'-'+phase+'.json')).write_text(json.dumps(args)+'\n')
  for k,v in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (p/(name+'-'+phase+'.'+k)).write_bytes(v)
  if a.returncode and phase!='wasm':break
 rows.append(row)
(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
