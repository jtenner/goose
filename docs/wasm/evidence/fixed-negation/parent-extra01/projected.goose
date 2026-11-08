struct S{n:i64,items:i64[2]}
recursive fn make()->S{return S{n:7,items:[8,-9]};}
fn main(){assert((-make()).n == -7);assert((-make()).items[1]==9);print("projected");}
