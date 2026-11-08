from pathlib import Path
import json
p=Path(__file__).parent;q=p/'parent04';q.mkdir(exist_ok=True);cases={};expected={}
prepare='recursive fn prepare(a:i64[2]&,b:i64[2]&){a[0]=7;a[1] = -8;b[0]=3;b[1]=4;print("before");}'
for name,ty,expr in [('owner_variable','i64[]','a+b'),('owner_varint','i64[varint]','a+b'),('owner_limited','i64[..]','a+b'),('owner_grow','i64[>..<]','a+b'),('owner_stored','i64[]','a')]:
 check='assert(c.len==2&&c[0]=='+('7' if expr=='a' else '10')+'&&c[1] == '+('-8' if expr=='a' else '-4')+');'
 if name=='owner_limited':check+='assert(c.cap==2);'
 cases[name]=prepare+f'fn main(){{var a:i64[2]=[0,0];var b:i64[2]=[0,0];prepare(a,b);var c:{ty}={expr};print("after");{check}assert(a[0]==7&&a[1] == -8&&b[0]==3&&b[1]==4);}}'
 expected[name]='before\nafter\n'
for count in [0,127,128,16383,16384]:
 name='prefix_'+str(count);checks=f'assert(c.len=={count});'+(f'assert(c[0]==3&&c[{count-1}]==3);' if count else '')
 cases[name]=f'fn main(){{var a:u8[{count}]=[1;{count}];var b:u8[{count}]=[2;{count}];print("before");var c:u8[varint]=a+b;print("after");{checks}}}'
 expected[name]='before\nafter\n'
cases.update({
'operators':'fn main(){var a:i64[2]=[7,-8];var b:i64[2]=[3,4];var sum:i64[]=a+b;var diff:i64[]=a-b;var product:i64[]=a*b;var quotient:i64[]=a/b;var remainder:i64[]=a%b;assert(sum[0]==10&&sum[1] == -4);assert(diff[0]==4&&diff[1] == -12);assert(product[0]==21&&product[1] == -32);assert(quotient[0]==2&&quotient[1] == -2);assert(remainder[0]==1&&remainder[1]==0);print("operators");}',
'effects':'var source:i64[2]=[7,-8];var calls:i64=0;recursive fn change()->i64[2]{calls++;source[0]=99;return[3,4];}fn main(){var c:i64[]=source+change();assert(c[0]==10&&c[1] == -4&&source[0]==99&&calls==1);print("effects");}',
'scalar_order':'var scalar:i64=3;var source:i64[2]=[7,8];var calls:i64=0;recursive fn values()->i64[2]{scalar=99;return[3,6];}recursive fn scale()->i64{calls++;source[0]=99;return 2;}fn main(){var a:i64[>..]=scalar*values();var b:i64[]=source*scale();assert(a[0]==9&&a[1]==18&&scalar==99);assert(b[0]==14&&b[1]==16&&source[0]==99&&calls==1);print("scalar_order");}',
'readonly':'recursive fn source(a:const i64[2]&)->const i64[2]&{return a;}fn main(){let a:const i64[2]=[7,-8];var c:i64[]=a;var d:i64[]=source(a);c[0]=99;d[1]=20;assert(a[0]==7&&a[1] == -8&&c[0]==99&&d[0]==7&&d[1]==20);print("readonly");}',
'defer_result':'recursive fn make()->i64[2]{var a:i64[2]=[7,-8];defer{a[0]=99;}return a;}fn main(){var c:i64[]=make();assert(c.len==2&&c[0]==7&&c[1] == -8);print("defer_result");}',
'early_return':'recursive fn choose(flag:bool)->i64{var a:i64[2]=[7,8];var c:i64[]=a*(if flag{return 55;}else{2});assert(c[0]==14&&c[1]==16);return c[0]+c[1];}fn main(){assert(choose(true)==55&&choose(false)==30);print("early_return");}',
'early_continue':'fn main(){var a:i64[2]=[7,8];var i=0;while i<4{print("head");var c:i64[]=a*(if i<3{i++;continue;}else{2});print("after");assert(c[0]==14&&c[1]==16);i++;}print("early_continue");}',
'function_data':'struct H{a:i64[2]}recursive fn build(a:const i64[2]&,b:const i64[2]&)->i64{var c:i64[]=a+b;return c[0]+c[1];}recursive fn parent()->i64{var held:H[]=[H{[20,30]},H{[1,2]}];let n=build(held[0].a,held[1].a);assert(held[0].a[0]==20&&held[1].a[1]==2);return n;}fn main(){var a:i64[2]=[7,-8];var b:i64[2]=[3,4];assert(build(a,b)==6&&parent()==53);print("function_data");}',
'zero_effects':'var calls:i64=0;recursive fn scale()->i64{calls++;return 2;}fn main(){var a:i64[0]=[];var v:i64[]=a*scale();var g:i64[>..]=a*scale();var s:i64[>..<]=a*scale();var l:i64[..]=a*scale();var p:i64[varint]=a*scale();assert(calls==5&&v.len==0&&g.len==0&&s.len==0&&l.len==0&&l.cap==0&&p.len==0);g.push(7);s.push(8);assert(g[0]==7&&s.pop()==8);print("zero_effects");}',
'large_growth':'fn main(){var a:i64[16384]=[7;16384];var b:i64[16384]=[3;16384];var c:i64[>..<]=a+b;assert(c.len==16384&&c[0]==10&&c[16383]==10);c[0]=99;c.push(9);assert(a[0]==7&&c.pop()==9&&c.len==16384);print("large_growth");}',
'padded_data':'struct S{a:f32,pad 2,b:f64}recursive fn prepare(a:S[2]&,b:S[2]&){a[0].a=1.25;a[0].b=45.125;a[1].a=2.0;a[1].b=3.5;b[0].a = -2.5;b[0].b = -37.25;b[1].a=3.0;b[1].b = -2.25;print("before");}fn main(){var a:S[2]=default<S[2]>();var b:S[2]=default<S[2]>();prepare(a,b);var c:S[]=a+b;print("after");assert(c.len==2&&c[0].a == -1.25&&c[0].b==7.875&&c[1].a==5.0&&c[1].b==1.25);}',
})
for n in cases:
 if n not in expected:expected[n]='head\n'*4+'after\nearly_continue\n' if n=='early_continue' else 'before\nafter\n' if n=='padded_data' else n+'\n'
(p/'cases-more.json').write_text(json.dumps(cases,indent=2)+'\n');(p/'expected-more.json').write_text(json.dumps(expected,indent=2)+'\n')
for n,s in cases.items():(q/(n+'.goose')).write_text(s+'\n')
s=(p/'parent02/checks.py').read_text().replace("'cases-values.json'","'cases-more.json'").replace("a.stdout==n.encode()+b'\\n'", "a.stdout==json.loads((p.parent/'expected-more.json').read_text())[n].encode()")
(q/'checks.py').write_text(s)
