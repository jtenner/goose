struct S{a:f32,pad 2,b:f64}
var source:S=S{a:1.25,b:45.125};
recursive fn observe(s:S&){print("after=",s.a==s.a,",",s.b==s.b);}
recursive fn prepare(s:S&){s.a=1.25;s.b=45.125;print("before");}
fn main(){prepare(source);var result:S=-source;observe(result);}
