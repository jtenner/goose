struct S{mark:u8,n:i64,tail:u16}fn main(){var a:S[varint]=[S{7,-8,900};127];assert(a.len==127&&a[126].n== -8&&a[126].tail==900);print("fill_count127");}
