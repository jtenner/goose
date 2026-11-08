fn main(){var source:u8[2]=[7,8];var c:u8[..256]=[1,2,3];c=source;assert(c.len==2&&c[0]==7&&c[1]==8);c.push(99);assert(c[2]==99);print("wide");}
