recursive fn make()->i64[2]{return[7,8];}
fn main(){var a:i64[]=[7,8];assert(a==make());print("guarded");}
