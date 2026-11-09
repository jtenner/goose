struct S{n:i64}fn main(){var a:S[u16]=[S{7};128];var b:S[varint]=copy(a);var c:S[u8]=copy(b);assert(b.len==128&&c[127].n==7);b[0].n=99;assert(a[0].n==7&&c[0].n==7);print("convert");}
