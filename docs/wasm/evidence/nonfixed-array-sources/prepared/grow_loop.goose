fn main(){var a:i64[>..]=[7,-8];var sum:i64=0;for i in 20{var b:i64[u16]=copy(a);sum+=b[0];if i==0{continue;}if i==19{break;}}assert(sum==140&&a[1]== -8);print("grow_loop");}
