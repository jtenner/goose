var a:i64[2]=[7,8];var b:i64[2]=[9,10];var p:i64[2]& = a;
recursive fn right()->i64[..3]{p .= b;return[7,8];}
fn main(){assert(p==right());assert(p .== &b);print("view_rebind");}
