var value:i64[2]=[3,4];inline fn use(a:i64[2],n:i64)->i64{return a[0]+n;}
recursive fn run(early:bool)->i64{return use(value,{if early{return 7;}3});}
fn main(){assert(run(true)==7);assert(run(false)==6);assert(value[0]==3);print("inline_exit");}
