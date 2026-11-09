var calls:i64=0;struct S{n:i64}fn main(){var a:S[u16]=[{calls++;S{calls}};2];assert(calls==1&&a[1].n==1);print("block_value");}
