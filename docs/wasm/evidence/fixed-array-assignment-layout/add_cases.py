from pathlib import Path
import json
p=Path(__file__).parent;q=p/'parent02';q.mkdir(exist_ok=True)
cases={
'copy':'fn main(){var a:i64[2]=[7,-8];var c:i64[..3]=[1,2,3];c=copy(a);assert(c.len==2&&c[0]==7&&c[1] == -8);print("copy");}',
'order':'struct H{values:u16[..3]}struct C{target:H&}var source:u16[2]=[77,88];recursive fn get(c:C&,next:H&)->u16[2]&{c.target .= next;return source;}fn main(){var first=H{[1,2,9]};var second=H{[3,4,8]};var c=C{first};c.target.values=get(c,second);assert(first.values.len==2&&first.values[0]==77&&first.values[1]==88&&second.values.len==3&&second.values[0]==3&&c.target .== &second);print("order");}',
'fat_order':'struct H{values:u16[..3]}struct C{target:H&}var source:u16[2]=[77,88];recursive fn get(c:C&,next:H&)->u16[2]&{c.target .= next;return source;}fn main(){var first:H[]=[H{[1,2,9]}];var second:H[]=[H{[3,4,8]}];var c=C{first[0]};c.target.values=get(c,second[0]);assert(first[0].values.len==2&&first[0].values[0]==77&&second[0].values.len==3&&second[0].values[0]==3&&c.target .== &second[0]);print("fat_order");}',
'function_data':'struct H{values:u16[..3]}struct S{values:u16[2]}recursive fn update(dst:u16[..3]&,src:u16[2]&){dst=src;}fn main(){var a:u16[2]=[7,8];var c:u16[..3]=[1,2,3];update(c,a);assert(c.len==2&&c[1]==8);var dest:H[]=[H{[1,2,3]}];var source:S[]=[S{[9,10]}];update(dest[0].values,source[0].values);assert(dest[0].values.len==2&&dest[0].values[1]==10&&source[0].values[0]==9);print("function_data");}',
'temporary_field':'struct S{a:i64[2]}var calls:i64=0;recursive fn make()->S{calls++;return S{[7,-8]};}fn main(){var c:i64[..3]=[1,2,3];c=make().a;assert(calls==1&&c.len==2&&c[0]==7&&c[1] == -8);print("temporary_field");}',
'reference_elements':'struct S{n:i64}fn main(){var a=S{7};var b=S{-8};var source:S&[2]=[a,b];var c:S&[..3]=[b,a,b];c=source;c[1].n=99;assert(c.len==2&&c[0].n==7&&b.n==99);print("reference_elements");}',
'padded':'struct S{a:f32,pad 2,b:f64}fn main(){var source:S[2]=[S{1.5,2.25},S{3.5,4.75}];var c:S[..3]=[S{9.5,10.25},S{11.5,12.75},S{13.5,14.25}];c=source;c[0].a=20.5;assert(c.len==2&&c[0].a==20.5&&c[1].b==4.75&&source[0].a==1.5);print("padded");}',
'wide':'fn main(){var source:u8[2]=[7,8];var c:u8[..256]=[1,2,3];c=source;assert(c.len==2&&c[0]==7&&c[1]==8);c.push(99);assert(c[2]==99);print("wide");}',
'owner_stored':'fn main(){var source:i64[2]=[7,-8];var c:i64[..3]=[1,2,3];print("before");c=source;print("after");assert(c.len==2&&c[0]==7&&c[1] == -8);}',
'owner_call':'recursive fn make()->i64[2]{return[7,-8];}fn main(){var c:i64[..3]=[1,2,3];print("before");c=make();print("after");assert(c.len==2&&c[0]==7&&c[1] == -8);}',
'owner_zero':'var calls:i64=0;recursive fn make()->i64[0]{calls++;print("inside");return[];}fn main(){var c:i64[..3]=[1,2,3];print("before");c=make();print("after");assert(calls==1&&c.len==0);}',
'owner_data':'struct H{before:u8,values:i64[..256],after:u16}fn main(){var source:i64[2]=[7,-8];var rows:H[]=[H{7,[1,2,3],65000}];print("before");rows[0].values=source;print("after");assert(rows[0].values.len==2&&rows[0].values[0]==7&&rows[0].values[1] == -8&&rows[0].before==7&&rows[0].after==65000);}',
}
for n,s in cases.items():(q/(n+'.goose')).write_text(s+'\n')
(p/'cases-more.json').write_text(json.dumps(list(cases),indent=2)+'\n');(p/'expected-more.json').write_text(json.dumps({n:('before\ninside\nafter\n' if n=='owner_zero' else 'before\nafter\n' if n.startswith('owner_') else n+'\n') for n in cases},indent=2)+'\n')
