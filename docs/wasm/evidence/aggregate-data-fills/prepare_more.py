from pathlib import Path
import json,hashlib
p=Path(__file__).parent;d=p/'prepared';cases={};meta={}
def add(name,s,expected=None,persistent=0):
 if expected is None:expected=name+'\n'
 assert name not in cases;cases[name]=s+'\n';meta[name]={'expected':expected,'persistent':persistent}
for width in [8,16,32,64]:
 for n in [0,3,128]:
  name=f'u{width}_count{n}';add(name,f'struct S{{mark:u8,n:i64,tail:u16}}fn main(){{var rows:S[u{width}]=[S{{7,-8,900}};{n}];assert(rows.len=={n});'+(f'assert(rows[0].mark==7&&rows[{n-1}].n== -8&&rows[{n-1}].tail==900);' if n else '')+f'print("{name}");}}')
add('u8_count255','struct S{n:u8}fn main(){var a:S[u8]=[S{73};255];assert(a.len==255&&a[254].n==73);print("u8_count255");}')
add('u16_count256','struct S{n:u8}fn main(){var a:S[u16]=[S{73};256];assert(a.len==256&&a[255].n==73);print("u16_count256");}')
add('reference','struct S{n:i64&}fn main(){var x:i64=7;var a:S[u16]=[S{n:x};3];a[1].n+=2;assert(x==9&&a[0].n==9&&a[2].n==9);print("reference");}')
add('optional_reference','struct S{n:i64&?}fn main(){var a:S[u8]=[S{n:null};3];assert(a[0].n==null&&a[2].n==null);print("optional_reference");}')
add('data_reference','struct S{n:i64&}fn main(){var seed:i64[]=[7,8];var a:S[u64]=[S{n:seed[1]};3];a[1].n+=2;assert(seed[1]==10&&a[0].n==10&&a[2].n==10);print("data_reference");}')
add('named_snapshot','struct S{n:i64,tail:u8}fn main(){var value:S=S{7,9};var a:S[u16]=[copy(value);3];value.n=99;a[0].tail=22;assert(a[1].n==7&&a[2].tail==9);print("named_snapshot");}')
add('default_value','var calls:i64=0;recursive fn next()->i64{calls++;return calls;}struct S{n:i64=next()}fn main(){var a:S[u8]=[default<S>();3];assert(calls==1&&a[0].n==1&&a[2].n==1);print("default_value");}')
add('default_zero','var calls:i64=0;recursive fn next()->i64{calls++;return calls;}struct S{n:i64=next()}fn main(){var a:S[u64]=[default<S>();0];assert(calls==1&&a.len==0);print("default_zero");}')
add('nested_snapshot','var calls:i64=0;recursive fn next()->i64{calls++;return calls;}struct S{n:i64}struct H{rows:S[..3]}fn main(){var a:H[u16]=[H{rows:[S{next()};2]};3];assert(calls==1&&a[0].rows.len==2&&a[2].rows[1].n==1);a[0].rows[1].n=99;assert(a[2].rows[1].n==1);print("nested_snapshot");}')
add('function_value','var calls:i64=0;struct S{n:i64}recursive fn value()->S{calls++;var keep:u8[]=[3;70000];assert(keep[69999]==3);return S{calls};}fn main(){var a:S[u32]=[value();3];assert(calls==1&&a[2].n==1);print("function_value");}')
add('conditional_value','struct S{n:i64}fn main(){var flag:bool=true;var a:S[u16]=[if flag{S{7}}else{S{9}};2];assert(a[0].n==7&&a[1].n==7);print("conditional_value");}')
add('block_value','var calls:i64=0;struct S{n:i64}fn main(){var a:S[u16]=[{calls++;S{calls}};2];assert(calls==1&&a[1].n==1);print("block_value");}')
add('loop_exits','struct S{n:i64}fn main(){var visits:i64=0;for i in 4{var a:S[u16]=[S{n:{if i==1{continue;}if i==3{break;}i+1}};2];assert(a[0].n==i+1&&a[1].n==i+1);visits++;}assert(visits==2);print("loop_exits");}')
add('zero_exit','struct S{n:i64}recursive fn run()->i64{var a:S[u16]=[S{n:{return 7;8}};0];return 0;}fn main(){assert(run()==7);print("zero_exit");}')
add('defer_exit','struct S{n:i64}recursive fn run()->i64{var a:S[u16]=[S{n:{defer{var bytes:u8[]=[7;70000];assert(bytes[69999]==7);}return 7;8}};0];return 0;}fn main(){assert(run()==7);print("defer_exit");}')
add('recursive','struct S{n:i64}recursive fn run(depth:i64)->i64{{var a:S[u16]=[S{depth};2];assert(a[1].n==depth);}if depth>0{return run(depth-1)+depth;}return 0;}fn main(){assert(run(4)==10);print("recursive");}')
add('global','struct S{mark:u8,n:i64,tail:u16}var a:S[u8]=[S{7,-8,900};3];fn main(){assert(a.len==3&&a[2].n== -8);a[0].mark=9;assert(a[1].mark==7);print("global");}',persistent=1)
add('dynamic','struct S{mark:u8,n:i64,tail:u16}recursive fn run(n:i64)->i64{var a:S[u16]=[S{7,n,900};3];return a[2].n;}fn main(){assert(run(-8)== -8);var keep:u8[]=[91];assert(run(17)==17);assert(keep[0]==91);print("dynamic");}')
add('standalone_variant','enum E{A{n:i64},B}fn main(){var a:E.A[u16]=[E.A{17};3];assert(a[2].n==17);a[0].n=99;assert(a[1].n==17);print("standalone_variant");}')
add('nested_enums','enum E{A{n:i64},B}struct S{a:E,rows:u8[..3]}fn main(){var a:S[u64]=[S{E.B,[9]};3];match a[2].a{B=>{},_=>assert(false)}assert(a[1].rows[0]==9);print("nested_enums");}')
add('fp_values','struct S{x:f32,y:f64,z:bool}fn main(){var a:S[u32]=[S{-1.25,3.5,true};3];assert(a[2].x== -1.25&&a[1].y==3.5&&a[0].z);print("fp_values");}')
for name,s in cases.items():(d/(name+'.goose')).write_text(s)
rows=[]
for f in sorted(d.glob('*.goose')):
 m=meta.get(f.stem,{'expected':f.stem+'\n','persistent':0});rows.append({'case':f.stem,'source_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),**m})
(p/'prepared-families.json').write_text(json.dumps(rows,indent=2)+'\n');print('Prepared',len(rows),'families, validity pending parent execution')
