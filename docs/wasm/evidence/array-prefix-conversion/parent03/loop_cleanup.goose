fn main(){var visits:i64=0;for i in 3{var a:u8[u8]=[7,8];var b:u8[varint]=copy(a);assert(b.len==2&&b[1]==8);if i==0{continue;}visits++;if i==1{break;}}assert(visits==1);print("loop_cleanup");}
