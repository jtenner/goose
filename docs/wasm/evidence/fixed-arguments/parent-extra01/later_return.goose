struct S{n:i64}
var value:S=S{n:1};recursive fn use(p:S,x:i64)->i64{return p.n+x;}
recursive fn run(early:bool)->i64{return use(value,{if early{return 7;}3});}
fn main(){assert(run(true)==7);assert(run(false)==4);assert(value.n==1);print("later_return");}
