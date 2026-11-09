struct S{mark:u8,n:i64,tail:u16}fn main(){var a:S[u64]=[S{7,-8,900},S{9,10,800}];var b:S[u64]=copy(a);b[0].n=31;assert(a.len==2&&b.len==2&&a[0].n== -8&&b[0].n==31&&b[1].tail==800);print("u64_copy");}
