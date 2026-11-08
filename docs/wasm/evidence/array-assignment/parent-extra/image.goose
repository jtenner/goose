struct P{a:u16[..4],b:u16[..4],guard:u16}
fn main(){var p:P=P{a:[1],b:[7,8],guard:13124};print("seed");p.a=p.b;print("copied");assert(p.a.len==2);assert(p.a[1]==8);assert(p.b.len==2);assert(p.guard==13124);}
