fn main(){var a:u8[16384]=[1;16384];var b:u8[16384]=[2;16384];print("before");var c:u8[varint]=a+b;print("after");assert(c.len==16384);assert(c[0]==3&&c[16383]==3);}
