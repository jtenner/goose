recursive fn make()->i64[2]{return[7,8];}
fn main(){var visits:i64=0;var hits:i64=0;for i in 4{visits++;if make()==({if i==0{continue;}if i==3{break;}[7,8]}){hits++;}}assert(visits==4);assert(hits==2);print("loop_exit");}
