var a:i64[2]=[7,8];
recursive fn change()->i64[2]{a[0]=9;return[7,8];}
fn main(){print(a==change());print(a[0]);}
