fn apply<F>(n:i64)->i64[..3]{F(n)}fn main(){var c=apply(7){n=>[n,n+1]};assert(c.len==2&&c[1]==8);print("callback");}
