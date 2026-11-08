var source:u16[..4]=[4660,22136];
var target:u16[..4]=[1];
recursive fn later()->i64{print("arg-live");source[0]=12;return 0;}
recursive fn make(p:u16[..4],x:i64)->u16[..4]{var saved:u16[..4]=p;print("callee-live");defer{saved[1]=9;print("defer");}return saved;}
fn main(){print("before");target=make(source,later());assert(target.len==2);assert(target[0]==4660);assert(target[1]==22136);assert(source[0]==12);print("after");}
