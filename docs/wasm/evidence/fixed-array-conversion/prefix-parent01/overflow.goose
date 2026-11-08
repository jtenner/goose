recursive fn scale()->i64{print("rhs");return 2;}fn main(){var a:i64[256]=[1;256];print("before");var c:i64[u8]=a*scale();print(c.len);}
