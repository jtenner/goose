struct S{mark:u8,n:i64,tail:u16}fn main(){var a:S[varint]=[S{7,-8,900};128];assert(a.len==128&&a[127].n== -8&&a[127].tail==900);print("fill_count128");}
