from pathlib import Path
import json
p=Path(__file__).parent
S='struct S{n:i64}recursive fn make()->S{return S{n:7};}'
R='recursive fn read(p:i64&)->i64{return p;}'
cases={
'field':S+R+'fn main(){assert(read(make().n)==7);PRINT}',
'element':'recursive fn make()->i64[2]{return[7,8];}'+R+'fn main(){assert(read(make()[1])==8);PRINT}',
'explicit_field':S+R+'fn main(){assert(read(&make().n)==7);PRINT}',
'explicit_element':'recursive fn make()->i64[2]{return[7,8];}'+R+'fn main(){assert(read(&make()[1])==8);PRINT}',
'constructor_field':'struct S{n:i64}'+R+'fn main(){assert(read((S{n:7}).n)==7);PRINT}',
'literal_element':R+'fn main(){assert(read([7,8][1])==8);PRINT}',
'nested_field':'struct I{n:i64}struct O{x:I}recursive fn make()->O{return O{x:I{n:7}};}recursive fn read(p:I&)->i64{return p.n;}fn main(){assert(read(make().x)==7);PRINT}',
'array_field':'struct O{x:i64[2]}recursive fn make()->O{return O{x:[7,8]};}recursive fn read(p:i64[2]&)->i64{return p[0]+p[1];}fn main(){assert(read(make().x)==15);PRINT}',
'nominal_element':'struct S{n:i64}recursive fn make()->S[2]{return[S{7},S{8}];}recursive fn read(p:S&)->i64{return p.n;}fn main(){assert(read(make()[1])==8);PRINT}',
'bool':'struct S{n:bool}recursive fn make()->S{return S{true};}recursive fn read(p:bool&)->bool{return p;}fn main(){assert(read(make().n));PRINT}',
'f32':'struct S{n:f32}recursive fn make()->S{return S{1.25};}recursive fn read(p:f32&)->f32{return p+0.5;}fn main(){assert(read(make().n)==1.75);PRINT}',
'f64_zero':'struct S{n:f64}recursive fn make()->S{return S{-0.0};}recursive fn read(p:f64&)->f64{return 1.0/p;}fn main(){assert(read(make().n)<0.0);PRINT}',
'packed_field':'struct S{m:u8,n:i64,t:u16}recursive fn make()->S{return S{17,-700,4660};}'+R+'fn main(){assert(read(make().n)== -700);PRINT}',
'write':S+'var calls:i64=0;recursive fn set(p:i64&){assert(p==7);p=99;assert(p==99);calls++;}fn main(){set(make().n);assert(calls==1);PRINT}',
'two_live':S+'var calls:i64=0;recursive fn noise()->i64{var a:i64[2]=[-99;2];calls++;return a[1];}recursive fn sum(p:i64&,q:i64&,x:i64)->i64{return p+q+x;}fn main(){assert(sum(make().n,make().n,noise())== -85&&calls==1);PRINT}',
'mixed_value':S+'recursive fn sum(p:i64&,q:S,x:i64)->i64{return p+q.n+x;}fn main(){assert(sum(make().n,S{11},3)==21);PRINT}',
'data_memory':S+'recursive fn read(p:i64&)->i64{var a:i64[]=[100,200];return p+a[0];}fn main(){var live:i64[]=[33];assert(read(make().n)==107&&live[0]==33);PRINT}',
'growth':S+'recursive fn noise()->i64{var a:i64[9000]=[-23;9000];assert(a[0]== -23&&a[8999]== -23);return 2;}recursive fn sum(p:i64&,x:i64)->i64{return p+x;}fn main(){assert(sum(make().n,noise())==9);PRINT}',
'later_return':S+'var calls:i64=0;recursive fn use(p:i64&,x:i64)->i64{calls++;return p+x;}recursive fn run(early:bool)->i64{return use(make().n,{if early{return 9;}3});}fn main(){assert(run(true)==9&&run(false)==10&&calls==1);PRINT}',
'later_continue':S+'var calls:i64=0;recursive fn use(p:i64&,x:i64)->i64{calls++;return p+x;}fn main(){var total:i64=0;for i in 0..3{total+=use(make().n,{if i==1{continue;}i});}assert(total==16&&calls==2);PRINT}',
'later_break':S+'var calls:i64=0;recursive fn use(p:i64&,x:i64)->i64{calls++;return p+x;}fn main(){var total:i64=0;for i in 0..3{total+=use(make().n,{if i==1{break;}i});}assert(total==7&&calls==1);PRINT}',
'stored_reference':'struct S{p:i64&}recursive fn make(p:i64&)->S{return S{p:p};}'+R+'fn main(){var a:i64[]=[41];assert(read(make(a[0]).p)==41);PRINT}',
'binary_field':'struct S{n:i64}recursive fn make()->S{return S{7};}'+R+'fn main(){assert(read((make()+S{2}).n)==9);PRINT}',
'binary_element':R+'fn main(){var a:i64[2]=[1,2];var b:i64[2]=[3,4];assert(read((a+b)[1])==6);PRINT}',
'owner':'struct S{m:u8,n:i64,t:u16}recursive fn make()->S{return S{17,700,4660};}recursive fn noise()->i64{var s:S=S{99,-77,88};print("argument-live");return s.n;}recursive fn use(p:i64&,x:i64)->i64{print("callee-live");return p+x;}fn main(){print("before");for i in 0..2{assert(use(make().n,noise())==623);print("after");}}'
}
rows=[]
for name,source in cases.items():
 expected='before\nargument-live\ncallee-live\nafter\nargument-live\ncallee-live\nafter\n' if name=='owner' else name+'\n'
 source=source.replace('PRINT','print("'+name+'");')+'\n';f=p/'sources'/(name+'.goose');f.parent.mkdir(exist_ok=True);f.write_text(source);rows.append({'case':name,'source':str(f),'expected':expected})
(p/'families.json').write_text(json.dumps(rows,indent=2)+'\n');print('prepared',len(rows),'families')
