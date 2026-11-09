struct S{n:u8}recursive fn gated(flag:bool){if flag{var a:S[u64]=[S{7};4294967288];assert(a.len==4294967288);}}fn main(){gated(false);print("guard");}
