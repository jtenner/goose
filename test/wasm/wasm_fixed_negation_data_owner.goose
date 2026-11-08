struct S{a:f32,pad 2,b:f64}
var source:S=S{a:1.25,b:45.125};
recursive fn prepare(s:S&){s.a=1.25;s.b=45.125;print("before");}
fn main(){prepare(source);var rows:S[]=[-source];print("after=",rows[0].a==rows[0].a,",",rows[0].b==rows[0].b);}
