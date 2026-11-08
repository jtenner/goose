struct S{a:f32,pad 2,b:f64}
var source:S[2]=[S{a:1.25,b:45.125},S{a:-2.5,b:-37.25}];
recursive fn prepare(s:S[2]&){s[0].a=1.25;s[1].b = -37.25;print("before");}
struct H{result:S[..3]}fn main(){prepare(source);var rows:H[]=[H{-source}];print("after=",rows[0].result.len,",",rows[0].result[0].a==rows[0].result[0].a,",",rows[0].result[0].b==rows[0].result[0].b);}
