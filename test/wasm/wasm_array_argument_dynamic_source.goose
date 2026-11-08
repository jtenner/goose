struct H{items:i64[2]}
recursive fn read(a:i64[2])->i64{a[0]=99;return a[1];}
recursive fn walk(rows:H[]&)->i64{return read(rows[0].items);}
fn main(){var first:H[]=[H{items:[3,4]}];var second:H[]=[H{items:[7,8]}];assert(walk(first)==4);assert(walk(second)==8);assert(first[0].items[0]==3);assert(second[0].items[0]==7);print("dynamic_source");}
