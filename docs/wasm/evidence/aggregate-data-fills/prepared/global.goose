struct S{mark:u8,n:i64,tail:u16}var a:S[u8]=[S{7,-8,900};3];fn main(){assert(a.len==3&&a[2].n== -8);a[0].mark=9;assert(a[1].mark==7);print("global");}
