struct S{a:u8,b:i64,c:u16}fn main(){var a:S[u64]=[S{7,-8,900},S{9,10,800}];var b:S[u8]=copy(a);assert(b.len==2&&b[0].b== -8&&b[1].c==800);b[0].a=99;assert(a[0].a==7);print("u64_to_u8");}
