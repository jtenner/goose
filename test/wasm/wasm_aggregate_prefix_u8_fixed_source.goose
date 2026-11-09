struct S{mark:u8,n:i64,tail:u16}fn main(){var a:S[2]=[S{7,-8,900},S{9,10,800}];var b:S[u8]=a;assert(b.len==2&&b[0].n== -8&&b[1].tail==800);b[0].n=31;assert(a[0].n== -8);print("u8_fixed_source");}
