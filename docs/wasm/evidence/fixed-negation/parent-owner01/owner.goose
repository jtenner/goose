struct S{a:f32,pad 2,b:f64}
var source:S=S{a:1.25,b:45.125};
recursive fn observe(s:S&){print("after=",s.a==s.a,",",s.b==s.b);}
fn main(){print("before");var result:S=-source;observe(result);}
