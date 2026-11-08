fn main(){var a:u8[128]=[1;128];var b:u8[128]=[2;128];print("before");var c:u8[varint]=a+b;print("after");assert(c.len==128);assert(c[0]==3&&c[127]==3);}
