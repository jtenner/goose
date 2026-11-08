enum E{Empty,Value{n:i64}}recursive fn make()->E.Empty{var x:E.Empty=default<E.Empty>();return x;}fn main(){let x:E.Empty=make();assert(x .== &x);print("enum_result");}
