struct H{leading:u16,values:u16[2]}
recursive fn set_h(dst:H&,src:H&){dst.values=src.values;}
fn main(){var a:H[]=[H{leading:1,values:[1,2]},H{leading:5,values:[5,6]}];var b:H[]=[H{leading:2,values:[7,8]}];set_h(a[0],b[0]);assert(a[0].leading==1);assert(a[0].values[1]==8);assert(a[1].leading==5);assert(a[1].values[0]==5);assert(b[0].leading==2);set_h(a[0],a[0]);assert(a[0].values[0]==7);print("field_carry");}
