struct H{items:i64[2]}
recursive fn left()->H{return H{items:[7,8]};}
recursive fn value(a:i64[2]&)->i64{return a[1]-92;}
recursive fn right()->i64[..3]{var scratch:i64[2]=[99,100];return[7,value(scratch)];}
fn main(){assert(left().items==right());print("view_projected");}
