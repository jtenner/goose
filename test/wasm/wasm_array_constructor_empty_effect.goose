var calls:i64=0;recursive fn tick()->i64{calls++;return calls;}
fn main(){var a:i64[0]=[];a=[tick();0];assert(calls==1);print("empty_effect");}
