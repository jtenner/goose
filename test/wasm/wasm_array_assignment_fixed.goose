fn main(){var a:u16[3]=[1,2,3];var b:u16[3]=[7,8,9];a=b;assert(a[0]==7);assert(a[2]==9);b[0]=10;assert(a[0]==7);a=a;assert(a[1]==8);print("fixed");}
