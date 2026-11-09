var calls:i64=0;recursive fn next()->i64{calls++;return calls;}struct S{n:i64=next()}fn main(){var a:S[u64]=[default<S>();0];assert(calls==1&&a.len==0);print("default_zero");}
