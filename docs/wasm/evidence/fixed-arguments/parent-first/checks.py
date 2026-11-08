from pathlib import Path
import subprocess,json,hashlib
r=Path('/home/dev/Projects/goose-wasm-backend');p=Path(__file__).parent;exe=Path('/tmp/goose-wasm-array-assignment-20261107/goose-tested');rows=[];commands=[]
cases={
'direct':'struct S{n:i64}\nrecursive fn alter(s:S)->i64{s.n=9;return s.n;}\nfn main(){var a:S=S{n:2};assert(alter(a)==9);assert(a.n==2);print("direct");}\n',
'inline':'struct S{n:i64}\ninline fn read(s:S)->i64{s.n}\nfn main(){var a:S=S{n:7};assert(read(a)==7);print("inline");}\n',
'callback':'struct S{n:i64}\nfn apply<F>(s:S&)->i64{F(copy(s))}\nfn main(){var a:S=S{n:7};var n:i64=apply(a){p=>p.n};assert(n==7);print("callback");}\n',
'order':'struct S{n:i64}\nrecursive fn change(s:S&)->i64{s.n=9;return 0;}\nrecursive fn read(s:S,unused:i64)->i64{return s.n+unused;}\nfn main(){var a:S=S{n:2};assert(read(a,change(a))==2);assert(a.n==9);print("order");}\n',
'isolation':'struct S{n:i64}\nrecursive fn read(a:S,b:S,original:S&)->i64{assert(&a .!= &b);assert(&a .!= original);a.n=9;assert(b.n==2);assert(original.n==2);return a.n;}\nfn main(){var a:S=S{n:2};assert(read(a,a,a)==9);assert(a.n==2);print("isolation");}\n',
'refs':'struct S{n:i64,link:i64&}\nrecursive fn alter(s:S)->i64{s.n=9;s.link+=1;return s.n;}\nfn main(){var x:i64[]=[7];var a:S=S{n:2,link:x[0]};assert(alter(a)==9);assert(a.n==2);assert(x[0]==8);assert(a.link .== &x[0]);print("refs");}\n',
'recursion':'struct S{n:i64}\nrecursive fn walk(s:S,depth:i64)->i64{if depth==0{return s.n;}var next:S=S{n:s.n+1};var result:i64=walk(next,depth-1);assert(next.n==s.n+1);return result;}\nfn main(){var a:S=S{n:1};assert(walk(a,3)==4);assert(a.n==1);print("recursion");}\n',
'enum':'enum E{A{n:i64},B}\nrecursive fn read(e:E)->i64{var result:i64=0;match e{A p=>{result=p.n;},B=>{result=7;}}return result;}\nfn main(){var a:E=E.A{n:9};assert(read(a)==9);assert(read(E.B)==7);print("enum");}\n',
'variant':'enum E{A{n:i64=7},B}\nrecursive fn read(p:E.A)->i64{return p.n;}\nfn main(){var a:E.A=default<E.A>();assert(read(a)==7);print("variant");}\n'}
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
  a=run(stem,'before',[exe,f'-O{opt}','--target','wasm','-o',module,source]);assert a.returncode==1 and b'by-value aggregate' in a.stderr and not module.exists(),a.stderr
  rows.append({'case':name,'opt':opt,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'native':'PASS','wasm_before':a.stderr.decode()});(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
print('PASS:',len(rows),'native cases and current fixed-argument ABI failures.')
