struct S{n:u8}recursive fn gated(flag:bool){if flag{var a:S[varint]=[S{7};2097152];assert(a.len==2097152);}}fn main(){gated(false);print("guarded_width4");}
