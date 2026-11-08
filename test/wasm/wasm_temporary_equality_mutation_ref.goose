var a:i64[2]=[7,8];
recursive fn change()->i64[2]&{a[0]=9;return a;}
fn main(){assert(!(a==change()));assert(a[0]==9);print("mutation_ref");}
