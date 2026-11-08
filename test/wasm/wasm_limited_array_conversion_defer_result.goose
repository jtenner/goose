recursive fn source()->u8[..3]{var a:u8[..3]=[7,8];defer a[0]=99;return a;}fn main(){var b:u8[]=source();assert(b.len==2&&b[0]==7);print("defer_result");}
