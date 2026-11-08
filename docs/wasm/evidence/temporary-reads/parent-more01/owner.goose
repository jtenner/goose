recursive fn make()->i64[2]{return[7,8];}
recursive fn touch(a:i64[2]&)->i64{a[0]-=98;return a[0];}
recursive fn index()->i64{var scratch:i64[2]=[99,100];print("index-live");return touch(scratch);}
fn main(){print("before");assert(make()[index()]==8);print("after");}
