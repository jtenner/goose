struct H{items:i64[2]}
recursive fn read(a:i64[2])->i64{a[0]=9;return a[1];}
fn main(){var rows:H[]=[H{items:[3,4]}];assert(read(rows[0].items)==4);assert(rows[0].items[0]==3);print("data");}
