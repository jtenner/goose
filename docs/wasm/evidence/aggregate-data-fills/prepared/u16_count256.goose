struct S{n:u8}fn main(){var a:S[u16]=[S{73};256];assert(a.len==256&&a[255].n==73);print("u16_count256");}
