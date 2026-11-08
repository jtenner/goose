struct S{x:i16,y:i16[2]}
struct H{head:i8,items:S[2]}
fn main(){var h:H=H{head:1,items:[S{x:2,y:[3,-4]},S{x:-5,y:[6,7]}]};var n:H=-h;assert(n.head == -1);assert(n.items[0].x == -2);assert(n.items[0].y[1]==4);assert(n.items[1].x==5);assert(n.items[1].y[0] == -6);assert(h.items[1].y[0]==6);print("nested");}
