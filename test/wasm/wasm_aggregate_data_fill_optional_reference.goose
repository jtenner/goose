struct S{n:i64&?}fn main(){var a:S[u8]=[S{n:null};3];assert(a[0].n==null&&a[2].n==null);print("optional_reference");}
