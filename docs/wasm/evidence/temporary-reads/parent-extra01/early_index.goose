recursive fn make()->i64[2]{return[7,8];}
recursive fn run(early:bool)->i64{return make()[{if early{return 7;}1}];}
fn main(){assert(run(true)==7);assert(run(false)==8);print("early_index");}
