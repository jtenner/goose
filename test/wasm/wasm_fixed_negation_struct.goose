struct S{a:i8,b:i64,c:i16[2]}
fn main(){var a:S=S{a:1,b:2,c:[-3,4]};var b:S=-a;assert(b.a == -1);assert(b.b == -2);assert(b.c[0]==3);assert(b.c[1] == -4);assert(a.a==1);print("struct");}
