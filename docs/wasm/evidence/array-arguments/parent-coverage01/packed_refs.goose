recursive fn change(a:i64&[2]){assert(a[0] .!= a[1]);a[1]+=1;}
fn main(){var first:i64[]=[3];var second:i64[]=[4];var refs:i64&[2]=[&first[0],&second[0]];change(refs);assert(first[0]==3);assert(second[0]==5);print("packed_refs");}
