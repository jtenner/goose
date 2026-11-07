struct S{n:i64}
fn main(){var visits:i64=0;for i in 4{var a:S[2]=[S{n:{if i==1{continue;}if i==3{break;}i+1}};2];assert(a[0].n==i+1);assert(a[1].n==i+1);visits++;print("step");}assert(visits==2);print("fill_exit");}
