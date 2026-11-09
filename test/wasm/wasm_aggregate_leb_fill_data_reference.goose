struct S{n:i64&}fn main(){var seed:i64[]=[7,8];var a:S[varint]=[S{n:seed[1]};3];a[1].n+=2;assert(seed[1]==10&&a[0].n==10&&a[2].n==10);print("data_reference");}
