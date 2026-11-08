var calls:i64=0;recursive fn make()->i64[0]{calls++;return[];}fn main(){var c:i64[..1]=[7];c=make();assert(calls==1&&c.len==0);c.push(9);assert(c[0]==9);print("zero");}
