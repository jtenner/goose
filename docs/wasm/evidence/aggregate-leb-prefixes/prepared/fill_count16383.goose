struct S{mark:u8,n:i64,tail:u16}fn main(){var a:S[varint]=[S{7,-8,900};16383];assert(a.len==16383&&a[16382].n== -8&&a[16382].tail==900);print("fill_count16383");}
