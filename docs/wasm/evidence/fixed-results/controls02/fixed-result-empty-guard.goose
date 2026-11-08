enum E{Empty,Value{n:i64}}
recursive fn make()->E.Empty{return default<E.Empty>();}
fn main(){var x:E.Empty=make();assert(x .== &x);print("empty_result");}
