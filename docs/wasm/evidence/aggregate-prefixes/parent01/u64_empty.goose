struct S{mark:u8,n:i64,tail:u16}fn main(){var a:S[u64]=[];var b:S[u64]=copy(a);assert(a.len==0&&b.len==0&&a .!= b);print("u64_empty");}
