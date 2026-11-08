recursive fn make(n:i64)->i64[2]{return[n,n+1];}fn main(){var total:i64=0;for i in 0..4{var c:i64[..3]=make(i);total+=c[1];if i<3{continue;}assert(c.len==2);}assert(total==10);print("continue");}
