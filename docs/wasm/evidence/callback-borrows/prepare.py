from pathlib import Path
import json,hashlib
r=Path(__file__).parent;repo=Path('/home/dev/Projects/goose-wasm-backend')
S='struct S{n:i64} recursive fn make()->S{return S{7};}'
A='recursive fn make()->i64[2]{return [7,8];}'
cases={
'field':S+'fn apply<F>()->i64{F(make().n)} fn main(){assert(apply(){p:i64& =>p+3}==10);PRINT}',
'element':A+'fn apply<F>()->i64{F(make()[1])} fn main(){assert(apply(){p:i64& =>p+3}==11);PRINT}',
'explicit_field':S+'fn apply<F>()->i64{F(&make().n)} fn main(){assert(apply(){p:i64& =>p+3}==10);PRINT}',
'explicit_element':A+'fn apply<F>()->i64{F(&make()[1])} fn main(){assert(apply(){p:i64& =>p+3}==11);PRINT}',
'nested':'struct I{n:i64} struct O{x:I} recursive fn make()->O{return O{I{7}};} fn apply<F>()->i64{F(make().x)} fn main(){assert(apply(){p:I& =>p.n+3}==10);PRINT}',
'array_field':'struct O{x:i64[2]} recursive fn make()->O{return O{[7,8]};} fn apply<F>()->i64{F(make().x)} fn main(){assert(apply(){p:i64[2]& =>p[0]+p[1]}==15);PRINT}',
'nominal_element':'struct S{n:i64} recursive fn make()->S[2]{return [S{7},S{8}];} fn apply<F>()->i64{F(make()[1])} fn main(){assert(apply(){p:S& =>p.n+3}==11);PRINT}',
'bool':'struct S{n:bool} recursive fn make()->S{return S{true};} fn apply<F>()->bool{F(make().n)} fn main(){assert(apply(){p:bool& =>p});PRINT}',
'f32':'struct S{n:f32} recursive fn make()->S{return S{1.25};} fn apply<F>()->f32{F(make().n)} fn main(){assert(apply(){p:f32& =>p+0.5}==1.75);PRINT}',
'f64':'struct S{n:f64} recursive fn make()->S{return S{-0.0};} fn apply<F>()->f64{F(make().n)} fn main(){assert(apply(){p:f64& =>1.0/p}<0.0);PRINT}',
'void':S+'var seen:i64=0;fn apply<F>(){F(make().n);} fn main(){apply(){p:i64& =>{assert(p==7);seen++;}};assert(seen==1);PRINT}',
'packed':'struct S{a:u8,n:i64,b:u16} recursive fn make()->S{return S{17,-700,4660};} fn apply<F>()->i64{F(make().n)} fn main(){assert(apply(){p:i64& =>p}== -700);PRINT}',
'data_memory':S+'fn apply<F>()->i64{var live:i64[]=[33];let n=F(make().n);assert(live[0]==33);n} fn main(){assert(apply(){p:i64& =>{var live:i64[]=[100];p+live[0]}}==107);PRINT}',
'two_live':S+'recursive fn noise()->i64{var s:S=S{-99};return s.n;} fn apply<F>()->i64{F(make().n,make().n,noise())} fn main(){assert(apply(){p:i64&,q:i64&,x:i64=>p+q+x}== -85);PRINT}',
'mixed_value':S+'fn apply<F>()->i64{F(make().n,S{11},3)} fn main(){assert(apply(){p:i64&,q:S,x:i64=>p+q.n+x}==21);PRINT}',
'growth':S+'recursive fn noise()->i64{var a:i64[9000]=[-23;9000];assert(a[0]== -23&&a[8999]== -23);return 2;} fn apply<F>()->i64{F(make().n,noise())} fn main(){assert(apply(){p:i64&,x:i64=>p+x}==9);PRINT}',
'later_return':S+'var calls:i64=0;fn apply<F>(early:bool)->i64{F(make().n,{if early{return 9;}3})} recursive fn run(early:bool)->i64{apply(early){p:i64&,x:i64=>{calls++;p+x}}} fn main(){assert(run(true)==9&&run(false)==10&&calls==1);PRINT}',
'later_continue':S+'var calls:i64=0;fn apply<F>()->i64{F(make().n)} fn main(){var sum:i64=0;for i in 0..3{sum+=apply(){p:i64& =>{if i==1{continue;}calls++;p+i}};}assert(sum==16&&calls==2);PRINT}',
'later_break':S+'var calls:i64=0;fn apply<F>()->i64{F(make().n)} fn main(){var sum:i64=0;for i in 0..3{sum+=apply(){p:i64& =>{if i==1{break;}calls++;p+i}};}assert(sum==7&&calls==1);PRINT}',
'binary_field':S+'fn apply<F>()->i64{F((make()+S{2}).n)} fn main(){assert(apply(){p:i64& =>p}==9);PRINT}',
'binary_element':'fn apply<F>(a:i64[2],b:i64[2])->i64{F((a+b)[1])} fn main(){assert(apply([1,2],[3,4]){p:i64& =>p}==6);PRINT}',
'owner':'struct S{m:u8,n:i64,t:u16} recursive fn make()->S{return S{17,700,4660};} recursive fn noise()->i64{var s:S=S{99,-77,88};print("argument-live");return s.n;} fn apply<F>()->i64{F(make().n,noise())} fn main(){print("before");for i in 0..2{assert(apply(){p:i64&,x:i64=>{print("body-live");p+x}}==623);print("after");}}'
}
rows=[]
for name,s in cases.items():
 expected='before\nargument-live\nbody-live\nafter\nargument-live\nbody-live\nafter\n' if name=='owner' else name+'\n'
 s=s.replace('PRINT','print("'+name+'");')+'\n';f=r/'sources'/(name+'.goose');f.write_text(s)
 rows.append({'case':name,'source':str(f),'expected':expected,'source_sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
(r/'families.json').write_text(json.dumps(rows,indent=2)+'\n');print('prepared',len(rows),'families')
