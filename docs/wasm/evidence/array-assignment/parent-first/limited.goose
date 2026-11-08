fn main(){var a:u16[..4]=[1];var b:u16[..4]=[7,8];a=b;assert(a.len==2);assert(a[1]==8);b.push(9);assert(a.len==2);print("limited");}
