struct H{a:i64[..3]}fn main(){var a:i64[2]=[7,-8];var rows:H[]=[H{-a}];assert(rows[0].a.len==2);assert(rows[0].a[0] == -7);assert(rows[0].a[1]==8);assert(a[0]==7);print("data");}
