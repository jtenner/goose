var choice:bool=true;recursive fn select()->bool{choice=!choice;return choice;}
fn main(){var a:i64[2]=if select(){[3,4]}else{[7,8]};var b:i64[2]=if select(){[3,4]}else{[7,8]};assert(a[0]==7);assert(b[0]==3);print("declared_control");}
