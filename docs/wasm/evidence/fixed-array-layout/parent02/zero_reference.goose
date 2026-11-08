var calls:i64=0;recursive fn source(a:i64[0]&)->i64[0]&{calls++;return a;}fn main(){var a:i64[0]=[];var c:i64[..1]=source(a);assert(c.len==0&&calls==1);print("zero_reference");}
