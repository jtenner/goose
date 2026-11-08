struct H{values:u16[3]}
recursive fn set(dst:u16[3]&,src:u16[3]&){dst=src;}
fn main(){var a:H[]=[H{values:[1,2,3]}];var b:H[]=[H{values:[7,8,9]}];set(a[0].values,b[0].values);assert(a[0].values[2]==9);var refs:u16[3]&[2]=[a[0].values,b[0].values];b[0].values[0]=11;refs[0]=refs[1];assert(a[0].values[0]==11);assert(refs[0] .== &a[0].values);print("fat_refs");}
