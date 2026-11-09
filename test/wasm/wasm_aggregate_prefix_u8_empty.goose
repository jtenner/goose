struct S{mark:u8,n:i64,tail:u16}fn main(){var a:S[u8]=[];var b:S[u8]=copy(a);assert(a.len==0&&b.len==0&&a .!= b);print("u8_empty");}
