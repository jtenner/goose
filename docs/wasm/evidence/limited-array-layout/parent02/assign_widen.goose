fn main(){var a:u8[..3]=[7,8];var b:u8[..256]=[1,2,3];b=a;assert(b.len==2&&b[0]==7&&b[1]==8);b.push(9);assert(b[2]==9&&a[0]==7);print("assign_widen");}
