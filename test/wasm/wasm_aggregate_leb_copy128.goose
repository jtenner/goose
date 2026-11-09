struct S{mark:u8,n:i64,tail:u16}fn main(){var a:S[varint]=[S{7,-8,900};128];var b:S[varint]=copy(a);assert(b.len==128&&b[127].n== -8);b[0].n=99;assert(a[0].n== -8&&b[1].n== -8);print("copy128");}
