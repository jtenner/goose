struct H{tag:u8,empty:i64[0]}recursive fn make()->i64[0]{var x:i64[0]=[];print("callee");return x;}fn main(){print("before");let h=H{90,make()};print("after");assert(h.tag==90&&h.empty.len==0);}
