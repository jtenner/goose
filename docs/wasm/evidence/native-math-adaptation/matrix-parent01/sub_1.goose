fn main(){var a:i64[2]=[7,-8];var b:i64[..3]=a-a;assert(b.len==2);assert(b[0]==0);assert(b[1]==0);assert(a[0]==7);assert(a[1] == -8);print("sub_1");}
