recursive fn set_values(dst:i64[2]&,n:i64){dst=[n,n+1];}
fn main(){var a:i64[2]=[1,2];set_values(a,7);assert(a[0]==7);assert(a[1]==8);struct H{a:i64[2]}var rows:H[]=[H{a:[1,2]}];set_values(rows[0].a,9);assert(rows[0].a[1]==10);print("refs");}
