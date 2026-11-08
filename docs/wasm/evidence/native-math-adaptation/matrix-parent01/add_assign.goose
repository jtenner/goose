fn main(){var a:i64[2]=[7,-8];var b:i64[..3]=[1,2,3];b=a+a;assert(b.len==2);assert(b[0]==14);assert(b[1]==-16);print("add_assign");}
