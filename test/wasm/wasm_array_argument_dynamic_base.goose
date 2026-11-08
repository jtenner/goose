struct S{n:i64}
recursive fn allocate(a:i64[2])->S{var data:i64[]=[a[0]];return S{n:data[0]+a[1]};}
recursive fn nested(a:i64[2])->S{var live:i64[]=[9];var s:S=allocate(a);assert(live[0]==9);return s;}
fn main(){var a:i64[2]=[3,4];var first:S=allocate(a);var second:S=nested(a);assert(first.n==7);assert(second.n==7);print("dynamic_base");}
