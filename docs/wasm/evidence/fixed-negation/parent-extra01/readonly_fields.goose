struct S{let a:i16,const b:i64}
fn main(){var a:S=S{a:7,b:-8};var b:S=-a;assert(b.a == -7);assert(b.b==8);print("readonly_fields");}
