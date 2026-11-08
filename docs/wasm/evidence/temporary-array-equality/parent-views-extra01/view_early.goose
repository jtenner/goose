recursive fn left()->i64[2]{return[7,8];}
recursive fn right()->i64[..3]{return[7,8];}
recursive fn run(early:bool)->bool{return left()==({if early{return true;}right()});}
fn main(){assert(run(true));assert(run(false));print("view_early");}
