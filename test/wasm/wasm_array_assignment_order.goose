struct H{values:u16[2]}
struct C{target:H&}
var source:u16[2]=[77,88];
recursive fn get(c:C&,next:H&)->u16[2]&{c.target .= next;return source;}
fn main(){var first:H=H{values:[1,2]};var second:H=H{values:[3,4]};var c:C=C{target:first};c.target.values=get(c,second);assert(first.values[0]==77);assert(second.values[0]==3);assert(c.target .== &second);print("order");}
