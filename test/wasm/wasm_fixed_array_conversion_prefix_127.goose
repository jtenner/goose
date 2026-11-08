fn main(){var a:u8[127]=[1;127];var b:u8[127]=[2;127];print("before");var c:u8[varint]=a+b;print("after");assert(c.len==127);assert(c[0]==3&&c[126]==3);}
