var calls:i64=0;recursive fn make()->i64[..4]{calls++;return[7,8];}
fn main(){assert(make().len==2);assert(calls==1);print("array_len");}
