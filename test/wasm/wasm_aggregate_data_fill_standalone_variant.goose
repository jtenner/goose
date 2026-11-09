enum E{A{n:i64},B}fn main(){var a:E.A[u16]=[E.A{17};3];assert(a[2].n==17);a[0].n=99;assert(a[1].n==17);print("standalone_variant");}
