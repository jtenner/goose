struct H{values:u16[3]}
fn main(){var a:H[]=[H{values:[1,2,3]}];var b:H[]=[H{values:[7,8,9]}];a[0].values=b[0].values;assert(a[0].values[2]==9);b[0].values[2]=10;assert(a[0].values[2]==9);print("data");}
