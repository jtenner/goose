struct H{values:u16[2]}
struct C{target:H&}
var source:u16[2]=[77,88];
recursive fn get(c:C&,next:H&)->u16[2]&{c.target .= next;return source;}
fn main(){var first:H[]=[H{values:[1,2]}];var second:H[]=[H{values:[3,4]}];var c:C=C{target:first[0]};c.target.values=get(c,second[0]);assert(first[0].values[0]==77);assert(second[0].values[0]==3);assert(c.target .== &second[0]);print("fat_order");}
