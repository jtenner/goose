struct S{n:i64}
struct H{s:S,items:i64[2]}
fn main(){var s:S=S{n:3};var a:i64[2]=[7,-8];var h:H=H{s:-s,items:-a};assert(h.s.n == -3);assert(h.items[1]==8);var rows:H[]=[H{s:-s,items:-a}];assert(rows[0].s.n == -3);assert(rows[0].items[0] == -7);assert(rows[0].items[1]==8);assert(s.n==3);assert(a[0]==7);print("field");}
