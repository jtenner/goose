recursive fn make(n:bool)->bool[2]{return[n,false];}
fn main(){assert(make(true)==[true,false]);assert(make(false)!=make(true));print("bool");}
