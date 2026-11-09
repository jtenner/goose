struct S{mark:u8,n:i64,tail:u16}var a:S[u16]=[S{7,-8,900}];fn main(){assert(a.len==1&&a[0].n== -8&&a[0].tail==900);print("u16_global");}
