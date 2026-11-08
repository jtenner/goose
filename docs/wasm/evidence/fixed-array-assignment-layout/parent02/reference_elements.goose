struct S{n:i64}fn main(){var a=S{7};var b=S{-8};var source:S&[2]=[a,b];var c:S&[..3]=[b,a,b];c=source;c[1].n=99;assert(c.len==2&&c[0].n==7&&b.n==99);print("reference_elements");}
