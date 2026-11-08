struct H{items:i64[2]}
recursive fn make()->H{return H{items:[7,8]};}
fn main(){var a:i64[2]=[7,8];assert(make().items==a);assert(a==make().items);print("projected");}
