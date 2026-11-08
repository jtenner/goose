from pathlib import Path
import json
p=Path(__file__).parent;q=p/'parent02';q.mkdir(exist_ok=True)
cases={
'capacity_equal':'fn main(){var a:i64[2]=[7,-8];var c:i64[..2]=a;assert(c.len==2&&c[1] == -8);}',
'zero':'var calls:i64=0;recursive fn make()->i64[0]{calls++;return[];}fn main(){var a:i64[0]=[];var c:i64[..0]=a;var d:i64[..1]=make();assert(c.len==0&&d.len==0&&calls==1);d.push(9);assert(d[0]==9);}',
'zero_reference':'var calls:i64=0;recursive fn source(a:i64[0]&)->i64[0]&{calls++;return a;}fn main(){var a:i64[0]=[];var c:i64[..1]=source(a);assert(c.len==0&&calls==1);}',
'field':'struct H{values:i64[..3]}fn main(){var a:i64[2]=[7,-8];var h=H{a};assert(h.values.len==2&&h.values[1] == -8);h.values.push(99);assert(h.values[2]==99&&a[0]==7);}',
'field_call':'struct H{values:i64[..3]}recursive fn make()->i64[2]{return[7,-8];}fn main(){var h=H{make()};assert(h.values.len==2&&h.values[1] == -8);}',
'field_data':'struct H{values:i64[..3]}recursive fn make()->i64[2]{return[7,-8];}fn main(){var a:i64[2]=[1,2];var rows:H[]=[H{a},H{make()}];assert(rows[0].values.len==2&&rows[0].values[1]==2&&rows[1].values.len==2&&rows[1].values[1] == -8);}',
'parameter_result':'recursive fn take(c:i64[..3])->i64[..4]{var a:i64[2]=[c[0]+1,c[1]];return a;}fn main(){var a:i64[2]=[7,-8];var c=take(a);assert(c.len==2&&c[0]==8&&c[1] == -8&&a[0]==7);}',
'callback':'fn apply<F>(n:i64)->i64[..3]{F(n)}fn main(){var c=apply(7){n=>[n,n+1]};assert(c.len==2&&c[1]==8);}',
'callback_parameter':'fn apply<F>(a:i64[..3])->i64{F(a)}fn main(){var a:i64[2]=[7,-8];assert(apply(a){p=>p[0]+p[1]} == -1);}',
'later_effect':'var a:i64[2]=[7,-8];recursive fn later()->i64{a[0]=99;return 0;}recursive fn take(c:i64[..3],n:i64)->i64{assert(n==0&&c.len==2);return c[0];}fn main(){assert(take(a,later())==7&&a[0]==99);}',
'defer':'recursive fn make()->i64[2]{var a:i64[2]=[7,-8];defer{a[0]=99;}return a;}fn main(){var c:i64[..3]=make();assert(c.len==2&&c[0]==7&&c[1] == -8);}',
'early_return':'recursive fn make(early:bool)->i64[2]{if early{return[7,-8];}return[1,2];}recursive fn take(early:bool)->i64{var c:i64[..3]=make(early);return c[0];}fn main(){assert(take(true)==7&&take(false)==1);}',
'continue':'recursive fn make(n:i64)->i64[2]{return[n,n+1];}fn main(){var total:i64=0;for i in 0..4{var c:i64[..3]=make(i);total+=c[1];if i<3{continue;}assert(c.len==2);}assert(total==10);}',
'readonly':'recursive fn source(a:const i64[2]&)->const i64[2]&{return a;}fn main(){let a:const i64[2]=[7,-8];var c:i64[..3]=source(a);c[0]=99;assert(a[0]==7&&c[0]==99);}',
'reference_elements':'struct S{n:i64}fn main(){var a=S{7};var b=S{-8};var rows:S&[2]=[a,b];var c:S&[..3]=rows;c[0].n=99;assert(a.n==99&&c.len==2&&c[1].n == -8);}',
'padded':'struct S{a:f32,pad 2,b:f64}fn main(){var a:S[2]=[S{1.5,2.25},S{3.5,4.75}];var c:S[..3]=a;c[0].a=9.5;assert(c.len==2&&c[0].a==9.5&&a[0].a==1.5&&c[1].b==4.75);}',
'global':'var a:i64[2]=[7,-8];var c:i64[..3]=a;fn main(){c[0]=99;assert(c.len==2&&c[0]==99&&a[0]==7);}',
'owner_stored':'recursive fn prepare(a:i64[2]&){a[0]=7;a[1] = -8;print("before");}fn main(){var a:i64[2]=[0,0];prepare(a);var c:i64[..3]=a;print("after");assert(c.len==2&&c[0]==7&&c[1] == -8);}',
'owner_call':'recursive fn prepare(a:i64[2]&){a[0]=7;a[1] = -8;print("before");}recursive fn source(a:i64[2]&)->i64[2]{return a;}fn main(){var a:i64[2]=[0,0];prepare(a);var c:i64[..3]=source(a);print("after");assert(c.len==2&&c[0]==7&&c[1] == -8);}',
}
for n,s in cases.items():
 if n.startswith('owner_'):end=''
 else:s=s[:-1]+'print("'+n+'");}';end=''
 (q/(n+'.goose')).write_text(s+'\n')
(p/'cases-more.json').write_text(json.dumps(list(cases),indent=2)+'\n')
(p/'expected-more.json').write_text(json.dumps({n:('before\nafter\n' if n.startswith('owner_') else n+'\n') for n in cases},indent=2)+'\n')
