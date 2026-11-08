var calls:i64=0;recursive fn make()->i64[0]{calls++;print("inside");return[];}fn main(){var c:i64[..3]=[1,2,3];print("before");c=make();print("after");assert(calls==1&&c.len==0);}
