struct S{n:i64}var a:S[varint]=[S{7};128];fn main(){var b:S[varint]=copy(a);assert(b.len==128&&b[127].n==7);print("global");}
