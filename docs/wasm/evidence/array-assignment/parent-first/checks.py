from pathlib import Path
import subprocess,json,hashlib
r=Path('/home/dev/Projects/goose-wasm-backend');p=Path(__file__).parent;exe=Path('/tmp/goose-wasm-aggregate-construction-20261107/goose-tested');rows=[];commands=[]
cases={
'fixed':'fn main(){var a:u16[3]=[1,2,3];var b:u16[3]=[7,8,9];a=b;assert(a[0]==7);assert(a[2]==9);b[0]=10;assert(a[0]==7);a=a;assert(a[1]==8);print("fixed");}\n',
'limited':'fn main(){var a:u16[..4]=[1];var b:u16[..4]=[7,8];a=b;assert(a.len==2);assert(a[1]==8);b.push(9);assert(a.len==2);print("limited");}\n',
'refs':'recursive fn set(dst:u16[3]&,src:u16[3]&){dst=src;}\nfn main(){var a:u16[3]=[1,2,3];var b:u16[3]=[7,8,9];set(a,b);assert(a[2]==9);var refs:u16[3]&[1]=[a];b[1]=10;refs[0]=b;assert(a[1]==10);print("refs");}\n',
'data':'struct H{values:u16[3]}\nfn main(){var a:H[]=[H{values:[1,2,3]}];var b:H[]=[H{values:[7,8,9]}];a[0].values=b[0].values;assert(a[0].values[2]==9);b[0].values[2]=10;assert(a[0].values[2]==9);print("data");}\n',
'nominal':'struct S{n:i64}\nfn main(){var a:S[2]=[S{n:1},S{n:2}];var b:S[2]=[S{n:7},S{n:8}];a=b;assert(a[0].n==7);assert(a[1].n==8);print("nominal");}\n',
'empty':'fn main(){var a:u8[0]=[];var b:u8[0]=[];a=b;assert(&a .!= &b);print("empty");}\n'}
def run(stem,label,args):
 a=subprocess.run(list(map(str,args)),cwd=r,capture_output=True,timeout=90)
 for ext,data in [('stdout',a.stdout),('stderr',a.stderr),('exit',(str(a.returncode)+'\n').encode())]:(p/(stem+'-'+label+'.'+ext)).write_bytes(data)
 commands.append({'name':stem+'-'+label,'args':list(map(str,args)),'exit':a.returncode});(p/'commands.json').write_text(json.dumps(commands,indent=2)+'\n');return a
for name,text in cases.items():
 source=p/(name+'.goose');source.write_text(text)
 for opt in [0,2]:
  stem=name+f'-O{opt}';c=p/(stem+'.c');native=p/(stem+'.native');module=p/(stem+'.wasm')
  for label,args in [('emit',[exe,f'-O{opt}','--standalone','-o',c,source]),('cc',['cc',c,'-pthread','-lm','-ldl','-o',native]),('native',[native])]:
   a=run(stem,label,args);assert not a.returncode,(name,label,a.stderr)
   if label=='native':assert a.stdout==(name+'\n').encode() and not a.stderr,(name,a.stdout,a.stderr)
  a=run(stem,'before',[exe,f'-O{opt}','--target','wasm','-o',module,source]);assert a.returncode==1 and (b'whole-array assignment' in a.stderr or b'whole-aggregate assignment' in a.stderr),a.stderr
  rows.append({'case':name,'opt':opt,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'native':'PASS','wasm_before':a.stderr.decode()});(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
print('PASS:',len(rows),'native cases and current exact-array assignment failures.')
