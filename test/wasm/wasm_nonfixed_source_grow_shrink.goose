fn main(){var a:i64[>..]=[7,-8];var b:i64[>..<]=copy(a);assert(b.len==2&&b[0]==7&&b[1]== -8);assert(b.pop()== -8);b.push(99);assert(a.len==2&&a[1]== -8&&b[1]==99);print("grow_shrink");}
