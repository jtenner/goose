struct S{n:u8}fn main(){var a:S[u8]=[S{73};255];assert(a.len==255&&a[254].n==73);print("u8_count255");}
