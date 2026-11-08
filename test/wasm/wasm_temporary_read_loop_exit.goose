recursive fn make()->i64[2]{return[7,8];}
fn main(){var visits:i64=0;var total:i64=0;for i in 4{visits++;total+=make()[{if i==0{continue;}if i==3{break;}1}];}assert(visits==4);assert(total==16);print("loop_exit");}
