struct S{n:i64}
struct H{s:S,items:i64[2]}
recursive fn make()->H{return H{s:S{n:7},items:[7,8]};}
fn main(){var s:S=make().s;var a:i64[2]=make().items;assert(s.n==7);assert(a[1]==8);print("copy_fields");}
