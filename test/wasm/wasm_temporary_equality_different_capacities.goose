recursive fn first()->u16[..3]{return[7,8];}
recursive fn second()->u16[..4]{return[7,8];}
fn main(){assert(first()==second());print("different_capacities");}
