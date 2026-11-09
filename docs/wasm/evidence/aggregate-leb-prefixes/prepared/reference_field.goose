struct S{n:i64}struct H{a:S[varint]&}fn main(){var a:S[varint]=[S{7};128];var holders:H[]=[H{a}];var b:S[varint]=copy(holders[0].a);assert(b.len==128&&b[127].n==7);print("reference_field");}
