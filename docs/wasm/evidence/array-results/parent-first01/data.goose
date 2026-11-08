struct H{items:i64[2]}
recursive fn make(n:i64)->i64[2]{[n,n+1]}
fn main(){var rows:H[]=[H{items:make(7)}];assert(rows[0].items[1]==8);rows[0].items=make(9);assert(rows[0].items[0]==9);print("data");}
