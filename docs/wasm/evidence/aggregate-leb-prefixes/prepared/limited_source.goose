struct S{n:i64}fn main(){var a:S[..4]=[S{7},S{9}];var b:S[varint]=copy(a);assert(b.len==2&&b[1].n==9);print("limited_source");}
