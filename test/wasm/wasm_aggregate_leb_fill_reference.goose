struct S{n:i64&}fn main(){var x:i64=7;var a:S[varint]=[S{n:x};3];a[1].n+=2;assert(x==9&&a[0].n==9&&a[2].n==9);print("reference");}
