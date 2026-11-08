fn main(){var a:u8[..3]=[7,8];for i in 0..40 {var b:u8[]=a;assert(b.len==2&&b[1]==8);if i<3{continue;}if i==20{break;}}print("loop");}
