struct S{mark:u8,n:i64,tail:u16}fn main(){var a:S[varint]=[S{7,-8,900};16384];assert(a.len==16384&&a[16383].n== -8&&a[16383].tail==900);print("fill_count16384");}
