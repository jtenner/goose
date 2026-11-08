struct H{a:u16[2]}
fn main(){var h:H[]=[H{a:[1,2]}];h[0].a=[3,4];assert(h[0].a[0]==3);assert(h[0].a[1]==4);print("field");}
