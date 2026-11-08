fn main(){var a:i64[2]=[7,-8];var b:i64[2]=[3,4];let c:i64[..3]=a+b;assert(c.len==2);assert(c[0]==10&&c[1] == -4);print("adapt");}
