var choice:bool=true;recursive fn select()->bool{choice=!choice;return choice;}
fn main(){var a:i64[2]=[1,2];a=if select(){[3,4]}else{[7,8]};assert(a[0]==7);a={let n=a[0];[n+1,n+2]};assert(a[0]==8);assert(a[1]==9);print("assigned_control");}
