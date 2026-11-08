struct S{n:i64}
struct H{lead:u8,s:S,tail:u16}
recursive fn make(n:i64)->S{return S{n:n};}
recursive fn outer(n:i64)->H{return H{lead:90,s:make(n),tail:23};}
fn main(){var h:H=outer(7);assert(h.lead==90);assert(h.s.n==7);assert(h.tail==23);print("nested_fields");}
