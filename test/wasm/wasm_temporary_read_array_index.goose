recursive fn make()->i64[2]{return[7,8];}
recursive fn index()->i64{var scratch:i64[2]=[99,100];return scratch[0]-98;}
fn main(){assert(make()[index()]==8);print("array_index");}
