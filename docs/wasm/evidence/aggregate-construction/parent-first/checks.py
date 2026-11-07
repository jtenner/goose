from pathlib import Path
import subprocess,json,hashlib
r=Path('/home/dev/Projects/goose-wasm-backend');p=Path(__file__).parent;exe=Path('/tmp/goose-wasm-constructor-assignment-20261107/build04/goose-tested');commands=[];rows=[]
cases={
'default':'var calls: i64=0; recursive fn tick()->i64 { calls++; return calls; }\nstruct S { n:i64=tick() }\nfn main(){ var a:S[3]=default<S[3]>(); assert(calls==3); assert(a[0].n==1);assert(a[1].n==2);assert(a[2].n==3);print("default");}\n',
'limited_default':'var calls:i64=0; recursive fn tick()->i64{calls++;return calls;}\nstruct S { n:i64=tick() }\nfn main(){var a:S[..3]=default<S[..3]>();assert(a.len==0);assert(calls==0);print("limited_default");}\n',
'fill':'var calls:i64=0; recursive fn tick()->i64{calls++;return calls;}\nstruct S { n:i64 }\nfn main(){var a:S[3]=[S{n:tick()};3];assert(calls==1);assert(a[0].n==1);assert(a[2].n==1);assert(&a[0] .!= &a[1]);print("fill");}\n',
'zero_fill':'var calls:i64=0; recursive fn tick()->i64{calls++;return calls;}\nstruct S { n:i64 }\nfn main(){var a:S[0]=[S{n:tick()};0];assert(calls==1);assert(a.len==0);print("zero_fill");}\n',
'limited_fill':'var calls:i64=0; recursive fn tick()->i64{calls++;return calls;}\nstruct S { n:i64 }\nfn main(){var a:S[..3]=[S{n:tick()};2];assert(calls==1);assert(a.len==2);assert(a[1].n==1);print("limited_fill");}\n',
'refs':'struct S { link:i64& }\nfn main(){var x:i64[]=[7];var old:S=S{link:x[0]};var a:S[2]=[old;2];assert(a[0].link .== &x[0]);assert(a[1].link .== &x[0]);a[1].link=9;assert(x[0]==9);assert(old.link==9);print("refs");}\n',
'nested':'struct S { n:i64=7 }\nstruct H { rows:S[2] }\nfn main(){var a:H=H{rows:default<S[2]>()};assert(a.rows[1].n==7);a=H{rows:[S{n:9};2]};assert(a.rows[0].n==9);assert(a.rows[1].n==9);print("nested");}\n',
'enums':'enum E { A{n:i64=7},B }\nfn main(){var a:E[2]=default<E[2]>();match a[1]{A p=>assert(p.n==7),_=>assert(false)}var b:E[2]=[E.B;2];match b[0]{B=>{},_=>assert(false)}print("enums");}\n'}
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
  a=run(stem,'before',[exe,f'-O{opt}','--target','wasm','-o',module,source]);assert a.returncode==1 and (b'aggregate array defaults' in a.stderr or b'aggregate array fills' in a.stderr),a.stderr
  rows.append({'case':name,'opt':opt,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'native':'PASS','wasm_before':a.stderr.decode()});(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
print('PASS:',len(rows),'native cases and exact current Wasm fill/default failures.')
