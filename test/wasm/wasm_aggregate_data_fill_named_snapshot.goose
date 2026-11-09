struct S{n:i64,tail:u8}fn main(){var value:S=S{7,9};var a:S[u16]=[copy(value);3];value.n=99;a[0].tail=22;assert(a[1].n==7&&a[2].tail==9);print("named_snapshot");}
