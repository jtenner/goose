struct H{values:i64[..3]}fn main(){var a:i64[2]=[7,-8];var h=H{a};assert(h.values.len==2&&h.values[1] == -8);h.values.push(99);assert(h.values[2]==99&&a[0]==7);print("field");}
