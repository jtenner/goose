struct S{n:u8}recursive fn gated(flag:bool){if flag{var a:S[varint]=[S{7};268435456];assert(a.len==268435456);}}fn main(){gated(false);print("guarded_width5");}
