from pathlib import Path
import subprocess,json,hashlib
r=Path('/home/dev/Projects/goose-wasm-backend');raw=Path(__file__).parent;p=raw/'parent03';p.mkdir(exist_ok=True)
exe=Path('/tmp/goose-wasm-fixed-array-assignment-layout-20261108/build01/goose-tested')
cases={
'wide16':'fn main(){var a:u8[..256];for(i in 0..256){a.push(i as u8);}var b:u8[..512]=a;assert(b.len==256&&b[255]==255);',
'wide32':'fn main(){var a:u8[..65536];for(i in 0..65536){a.push(i as u8);}var b:u8[..65537]=a;assert(b.len==65536&&b[65535]==255);',
'prefix32down':'fn main(){var a:u8[..65536]=[7,8];var b:u8[..3]=a;assert(b.len==2&&b[1]==8);',
'prefix32up':'fn main(){var a:u8[..256]=[7,8];var b:u8[..65536]=a;assert(b.len==2&&b[1]==8);',
'zero_up':'fn main(){var a:u8[..0];var b:u8[..256]=a;assert(b.len==0);b.push(7);assert(b[0]==7);',
'zero_down':'fn main(){var a:u8[..256];var b:u8[..0]=a;assert(b.len==0);',
'exact_shrink':'fn main(){var a:u8[..256]=[7,8,9];var b:u8[..3]=a;assert(b.len==3&&b[2]==9);',
'return':'recursive fn make(a:u8[..3])->u8[..256]{return a;}fn main(){var a:u8[..3]=[7,8];var b=make(a);assert(b.len==2&&b[1]==8);',
'parameter':'recursive fn take(a:u8[..256])->i64{return a.len+a[1];}fn main(){var a:u8[..3]=[7,8];assert(take(a)==10);',
'inline':'inline fn make(a:u8[..3])->u8[..256]{return a;}fn main(){var a:u8[..3]=[7,8];var b=make(a);assert(b.len==2&&b[1]==8);',
'callback':'fn apply<F>(a:u8[..3])->u8[..256]{F(a)}fn main(){var a:u8[..3]=[7,8];var b=apply(a){p=>p};assert(b.len==2&&b[1]==8);',
'callback_parameter':'fn apply<F>(a:u8[..3])->i64{F(a)}fn main(){var a:u8[..3]=[7,8];assert(apply(a){p:u8[..256]=>p.len+p[1]}==10);',
'snapshot':'recursive fn take(a:u8[..256],n:i64)->i64{return a.len+n;}recursive fn change(a:u8[..3]&)->i64{a.push(9);return 10;}fn main(){var a:u8[..3]=[7,8];assert(take(a,change(a))==12&&a.len==3);',
'source_effect':'recursive fn change(a:u8[..256]&)->u8[..256]&{a.push(8);return a;}fn main(){var a:u8[..256]=[7];var b:u8[..3]=change(a);assert(b.len==2&&b[1]==8);',
'padded':'struct S{a:f32,pad 2,b:f64}fn main(){var a:S[..3]=[S{1.5,-2.0},S{3.5,4.0}];var b:S[..5]=a;assert(b.len==2&&b[1].a==3.5&&b[0].b== -2.0);',
'ref_elements':'struct S{n:i64}recursive fn make(a:S&,b:S&)->S&[..3]{return[a,b];}fn main(){var rows:S[]=[S{7},S{8}];var b:S&[..5]=make(rows[0],rows[1]);b[0].n=99;assert(b.len==2&&rows[0].n==99&&b[1].n==8);',
'call_field':'struct S{xs:u8[..3]}recursive fn make()->S{return S{[7,8]};}fn main(){var b:u8[..256]=make().xs;assert(b.len==2&&b[1]==8);',
'order':'struct H{xs:u16[..256]}struct C{target:H&}var source:u16[..3]=[77,88];recursive fn get(c:C&,next:H&)->u16[..3]&{c.target .= next;return source;}fn main(){var first=H{[1,2,9]};var second=H{[3,4,8]};var c=C{first};c.target.xs=get(c,second);assert(first.xs.len==2&&first.xs[0]==77&&second.xs.len==3&&second.xs[0]==3&&c.target .== &second);',
'fat_order':'struct H{xs:u16[..256]}struct C{target:H&}var source:u16[..3]=[77,88];recursive fn get(c:C&,next:H&)->u16[..3]&{c.target .= next;return source;}fn main(){var first:H[]=[H{[1,2,9]}];var second:H[]=[H{[3,4,8]}];var c=C{first[0]};c.target.xs=get(c,second[0]);assert(first[0].xs.len==2&&first[0].xs[0]==77&&second[0].xs.len==3&&second[0].xs[0]==3&&c.target .== &second[0]);',
'dynamic_data':'struct A{xs:u8[..3]}struct B{xs:u8[..256]}recursive fn test(a:A&){var b:B[]=[B{a.xs}];assert(b[0].xs.len==2&&b[0].xs[1]==8);b[0].xs=a.xs;assert(b[0].xs[0]==7);}fn main(){var a=A{[7,8]};test(a);var rows:A[]=[a];test(rows[0]);',
'owner':'struct S{a:f32,pad 2,b:f64}fn main(){var a:S[..3]=[S{1.5,-2.0},S{3.5,4.0}];print("before");var b:S[..5]=a;print("after");assert(b.len==2&&b[1].a==3.5);',
'owner_data':'struct A{before:u8,xs:u8[..3],after:u16}struct B{before:u8,xs:u8[..256],after:u16}recursive fn prepare(a:const u8[..3]&)->const u8[..3]&{print("before");return a;}fn main(){var source:A[]=[A{9,[7,8],60000}];var target:B[]=[B{7,prepare(source[0].xs),65000}];print("after");assert(target[0].xs.len==2&&target[0].xs[1]==8&&target[0].after==65000);',
}
rows=[]
def run(name,kind,args):
 a=subprocess.run(list(map(str,args)),cwd=r,capture_output=True,timeout=120)
 for k,v in [('stdout',a.stdout),('stderr',a.stderr),('exit',str(a.returncode).encode()+b'\n')]: (p/(name+'-'+kind+'.'+k)).write_bytes(v)
 (p/(name+'-'+kind+'.json')).write_text(json.dumps(list(map(str,args)))+'\n');return a
for name,body in cases.items():
 source=body+'}\n' if name.startswith('owner') else body+f'print("{name}");}}\n'
 f=p/(name+'.goose');f.write_text(source);row={'case':name,'source_sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
 a=run(name,'emit',[exe,'--standalone','-o',p/(name+'.c'),f]);row['emit_exit']=a.returncode
 if not a.returncode:
  a=run(name,'cc',['cc',p/(name+'.c'),'-pthread','-lm','-ldl','-o',p/(name+'.native')]);row['cc_exit']=a.returncode
  if not a.returncode:
   a=run(name,'native',[p/(name+'.native')]);row['native_exit']=a.returncode
   if not a.returncode:
    expected=b'before\nafter\n' if name.startswith('owner') else (name+'\n').encode();assert a.stdout==expected,(name,a.stdout,expected)
    a=run(name,'wasm',[exe,'--target','wasm','-o',p/(name+'.wasm'),f]);row['wasm_exit']=a.returncode
    (r/'test/wasm'/('wasm_limited_array_layout_'+name+'.goose')).write_bytes(f.read_bytes());(r/'test/expected'/('wasm_limited_array_layout_'+name+'.out')).write_bytes(expected)
 rows.append(row)
(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
