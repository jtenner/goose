recursive fn fixed()->i64[2]{return[7,8];}
recursive fn limited()->i64[..3]{return[7,8];}
fn main(){assert(limited()==fixed());assert(!(limited()!=fixed()));print("view_reverse");}
