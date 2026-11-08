struct H{items:i64[2]}
recursive fn make()->H{return H{items:[7,8]};}
recursive fn index()->i64{var scratch:i64[2]=[99,100];return scratch[0]-98;}
fn main(){assert(make().items[index()]==8);print("field_array_index");}
