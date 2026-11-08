fn main(){var a:i32[2][2]=[[1,2],[3,4]];let b:i32[2][..3]=-a;assert(b.len==2);assert(b[0][1] == -2);assert(b[1][0] == -3);print("array");}
