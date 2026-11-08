var source:u16[..4]=[4660,22136];
recursive fn later()->i64{print("arg-live");source[0]=12;return 0;}
recursive fn consume(p:u16[..4],x:i64)->i64{print("callee-live");defer{p[1]=9;print("callee-defer");}assert(p.len==2);assert(p[0]==4660);assert(p[1]==22136);return p[0]+x;}
fn main(){print("seed");let result=consume(source,later());assert(result==4660);assert(source[0]==12);assert(source[1]==22136);print("done");}
