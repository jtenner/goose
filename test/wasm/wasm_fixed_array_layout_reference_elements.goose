struct S{n:i64}fn main(){var a=S{7};var b=S{-8};var rows:S&[2]=[a,b];var c:S&[..3]=rows;c[0].n=99;assert(a.n==99&&c.len==2&&c[1].n == -8);print("reference_elements");}
