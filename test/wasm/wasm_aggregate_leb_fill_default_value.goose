var calls:i64=0;recursive fn next()->i64{calls++;return calls;}struct S{n:i64=next()}fn main(){var a:S[varint]=[default<S>();3];assert(calls==1&&a[0].n==1&&a[2].n==1);print("default_value");}
