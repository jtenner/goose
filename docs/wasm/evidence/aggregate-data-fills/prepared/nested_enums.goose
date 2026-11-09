enum E{A{n:i64},B}struct S{a:E,rows:u8[..3]}fn main(){var a:S[u64]=[S{E.B,[9]};3];match a[2].a{B=>{},_=>assert(false)}assert(a[1].rows[0]==9);print("nested_enums");}
