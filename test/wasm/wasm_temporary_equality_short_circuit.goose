var calls:i64=0;recursive fn make(n:i64)->i64[2]{calls++;return[n,n+1];}
fn main(){let a=false&&(make(1)==make(2));assert(!a);assert(calls==0);let b=true||(make(1)==make(2));assert(b);assert(calls==0);assert(true&&(make(1)==make(1)));assert(calls==2);assert(false||(make(1)!=make(2)));assert(calls==4);print("short_circuit");}
