struct H{items:i64[2]}
var index:i64=1;
recursive fn make()->i64[2]{print("rhs");return[7,8];}
fn main(){var rows:H[]=[H{items:[1,2]}];print("before");rows[index].items=make();print("after");}
