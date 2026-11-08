recursive fn make()->i64[2]{return[7,8];}
fn main(){assert(make()==[7,8]);assert([7,8]==make());assert(([7,8])==([7,8]));print("literal_result");}
