recursive fn make()->i64[2]{return[7,8];}
recursive fn run(early:bool)->bool{return make()=={if early{return true;}[7,8]};}
fn main(){assert(run(true));assert(run(false));print("early");}
