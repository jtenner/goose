struct S{mark:u8,n:i64,tail:u16}fn main(){var a:S[u16]=[];var b:S[u16]=copy(a);assert(a.len==0&&b.len==0&&a .!= b);print("u16_empty");}
