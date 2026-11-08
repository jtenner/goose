struct S{a:f32,pad 2,b:f64}
var source:S=S{a:1.25,b:45.125};
fn main(){print("before");var rows:S[]=[-source];print("after=",rows[0].a==rows[0].a,",",rows[0].b==rows[0].b);}
