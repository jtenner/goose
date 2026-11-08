struct H{items:i64[2]}
struct S{link:H&}
recursive fn make(p:H&)->S{return S{link:p};}
recursive fn index()->i64{var scratch:i64[2]=[98,100];return scratch[0]-97;}
fn main(){var h:H=H{items:[7,8]};assert(make(h).link.items[index()]==8);var a:i64[2]=make(h).link.items;assert(a[0]==7);assert(a[1]==8);print("nested_ref");}
