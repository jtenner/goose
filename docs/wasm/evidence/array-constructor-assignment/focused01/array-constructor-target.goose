struct H{a:i64[2]}
var index:i64=1;
recursive fn effect()->i64{print("rhs");return 9;}
fn main(){var rows:H[]=[H{a:[1,2]}];print("before");rows[index].a=[effect(),10];print("after");}
