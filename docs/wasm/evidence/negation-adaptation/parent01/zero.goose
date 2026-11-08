var calls:i64=0;recursive fn empty()->i64[0]{calls++;return [];}fn main(){let b:i64[..3]=-empty();assert(calls==1);assert(b.len==0);print("zero");}
