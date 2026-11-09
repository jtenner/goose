struct S{n:u8}recursive fn gated(flag:bool){if flag{var a:S[u64]=[S{7};4294967295];assert(a.len==4294967295);}}fn main(){gated(false);print("guard");}
