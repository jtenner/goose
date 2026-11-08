enum E{Empty,Value{n:i64}}
recursive fn take(x:E.Empty)->i64{print("inside");return 1;}
fn main(){var x:E.Empty=default<E.Empty>();print(take(x));}
