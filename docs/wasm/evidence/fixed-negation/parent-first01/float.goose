struct S{a:f32,b:f64}
fn main(){var s:S=S{a:0.0,b:-0.0};var t:S=-s;assert(1.0/t.a<0.0);assert(1.0/t.b>0.0);print("float");}
