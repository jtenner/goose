var source:i64[2]=[7,-8];var target:i64[..3]=[1,2,3];fn main(){target=source;assert(target.len==2&&target[0]==7&&target[1] == -8&&source[0]==7);print("global");}
