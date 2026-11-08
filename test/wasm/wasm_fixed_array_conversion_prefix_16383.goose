fn main(){var a:u8[16383]=[1;16383];var b:u8[16383]=[2;16383];print("before");var c:u8[varint]=a+b;print("after");assert(c.len==16383);assert(c[0]==3&&c[16382]==3);}
