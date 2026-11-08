var calls:i64=0;recursive fn scale()->i64{calls++;return 2;}fn main(){var a:i64[0]=[];a*=scale();assert(a.len==0&&calls==1);print("zero");}
