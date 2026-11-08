enum E{Empty,Value{n:i64}}recursive fn take(x:E.Empty)->i64{assert(x .== &x);return 55;}fn main(){var x:E.Empty=E.Empty;assert(take(x)==55);print("enum_parameter");}
