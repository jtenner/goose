var target:i64[2]=[1,2];var divisor:i64=0;
recursive fn make()->i64[2]{return[9,8/divisor];}
fn main(){print("before");target=make();print("after");}
