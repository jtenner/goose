var calls:i64=0;recursive fn make()->i64[0]{var a:i64[0]=[];defer{calls++;print("defer");}print("inside");return a;}fn main(){let a=make();assert(a.len==0&&calls==1);print("defer_done");}
