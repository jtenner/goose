from pathlib import Path
import json
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend')
cases={
'integer_edges':'fn main(){var a:i8[2]=[-128,127];var b:i8[2]=[-1,-3];let q=a/b;let m=a%b;assert(q[0] == -128&&q[1] == -42);assert(m[0]==0&&m[1]==1);var c:i16[2]=[-32768,-13];var d:i16[2]=[-1,5];let r=c/d;let s=c%d;assert(r[0] == -32768&&r[1] == -2);assert(s[0]==0&&s[1]==2);var e:i32[2]=[-2147483648,-13];var f:i32[2]=[-1,-5];let g=e/f;let h=e%f;assert(g[0] == -2147483648&&g[1]==2);assert(h[0]==0&&h[1]==2);var i:i64[2]=[-9223372036854775808,-13];var j:i64[2]=[-1,-9223372036854775808];let k=i%j;assert(k[0]==0&&k[1]==9223372036854775795);print("integer_edges");}',
'ieee':'struct S{n:f32,i:f32}fn main(){var z:f32=0.0;var a=S{z/z,1.0/z};var b=S{1.0,2.0};let c=a+b;let d=a/b;let e=a%b;assert(c.n!=c.n&&c.i==a.i);assert(d.n!=d.n&&d.i==a.i);assert(e.n!=e.n&&e.i!=e.i);var zero:f64=0.0;var x:f64[2]=[zero/zero,1.0/zero];var y:f64[2]=[1.0,2.0];let q=x/y;let rem=x%y;assert(q[0]!=q[0]&&q[1]==x[1]);assert(rem[0]!=rem[0]&&rem[1]!=rem[1]);print("ieee");}',
'recursion':'recursive fn build(n:i64)->i64[2]{if n==0{return [1,2];}return build(n-1)+[1,2];}fn main(){let c=build(4);assert(c[0]==5&&c[1]==10);print("recursion");}',
'argument_result':'var a:i64[2]=[7,-8];var b:i64[2]=[3,4];recursive fn later()->i64{a[0]=99;return 0;}recursive fn take(c:i64[..3],n:i64)->i64[..3]{assert(n==0&&c.len==2);assert(c[0]==10&&c[1] == -4);c[0]+=1;return c;}fn main(){let c=take(a+b,later());assert(c.len==2&&c[0]==11&&c[1] == -4);assert(a[0]==99);print("argument_result");}',
'nested_destination':'struct H{values:i64[..3]}var indices:i64=0;recursive fn index()->i64{indices++;return 0;}fn main(){var a:i64[2]=[7,-8];var b:i64[2]=[3,4];let h=H{a+b};assert(h.values.len==2&&h.values[0]==10&&h.values[1] == -4);var rows:H[]=[H{a-b}];assert(rows[0].values.len==2&&rows[0].values[0]==4&&rows[0].values[1] == -12);rows[index()].values=a+b;assert(indices==1);assert(rows[0].values.len==2&&rows[0].values[0]==10&&rows[0].values[1] == -4);print("nested_destination");}',
'function_data':'struct S{x:i64,y:i64}recursive fn run(a:const S&,b:const S&)->i64{var rows:S[]=[a+b];return rows[0].x+rows[0].y;}recursive fn parent()->i64{var held:S[]=[S{20,30},S{1,2}];let n=run(held[0],held[1]);assert(held[0].x==20&&held[0].y==30);assert(held[1].x==1&&held[1].y==2);return n;}fn main(){var a=S{7,-8};var b=S{3,4};assert(run(a,b)==6);assert(parent()==53);print("function_data");}',
'callback':'fn apply<F>(a:i64[2],b:i64[2])->i64[2]{return F(a,b);}fn main(){let c=apply([7,-8],[3,4]){a:i64[2],b:i64[2]=>a+b};assert(c[0]==10&&c[1] == -4);print("callback");}'
}
(p/'cases-extra.json').write_text(json.dumps(cases,indent=2)+'\n')
allcases=json.loads((p/'positive-cases.json').read_text());allcases.update(cases);(p/'positive-cases02.json').write_text(json.dumps(allcases,indent=2)+'\n')
for n,s in cases.items():
 (p/'parent04'/(n+'.goose')).write_text(s+'\n');(r/'test/wasm'/('wasm_fixed_binary_'+n+'.goose')).write_text(s+'\n');(r/'test/expected'/('wasm_fixed_binary_'+n+'.out')).write_text(n+'\n')
p=r/'test/wasm_backend.py';s=p.read_text().replace("'wasm_fixed_binary_data_owner') else 'no-data'", "'wasm_fixed_binary_data_owner', 'wasm_fixed_binary_nested_destination',\n                                            'wasm_fixed_binary_function_data') else 'no-data'");p.write_text(s)
