struct S{n:i64}
inline fn read(s:S)->i64{s.n}
fn main(){var a:S=S{n:7};assert(read(a)==7);print("inline");}
