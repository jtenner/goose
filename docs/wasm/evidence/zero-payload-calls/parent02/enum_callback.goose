enum E{Empty,Value{n:i64}}fn apply<F>(a:E.Empty)->E.Empty{return F(a);}fn main(){var a:E.Empty=E.Empty;let b:E.Empty=apply(a){x:E.Empty=>x};assert(&a .!= &b);print("enum_callback");}
