struct S{n:i64}fn main(){var a:S[u8]=[S{7},S{8}];for &s in a{s.n+=10;}assert(a[0].n==17&&a[1].n==18);print("u8_byref");}
