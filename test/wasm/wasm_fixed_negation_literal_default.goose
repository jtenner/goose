struct S{a:i16=3,b:i64=-4}
struct F{x:f32,y:f64}
fn main(){var a:S=-(S{a:7,b:-8});assert(a.a == -7);assert(a.b==8);var b:S=-default<S>();assert(b.a == -3);assert(b.b==4);var c:i64[2]=-([1,-2]);assert(c[0] == -1);assert(c[1]==2);var f:F=-default<F>();assert(1.0/f.x<0.0);assert(1.0/f.y<0.0);print("literal_default");}
