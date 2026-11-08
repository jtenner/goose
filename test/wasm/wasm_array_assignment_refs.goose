recursive fn set(dst:u16[3]&,src:u16[3]&){dst=src;}
fn main(){var a:u16[3]=[1,2,3];var b:u16[3]=[7,8,9];set(a,b);assert(a[2]==9);var refs:u16[3]&[1]=[a];b[1]=10;refs[0]=b;assert(a[1]==10);print("refs");}
