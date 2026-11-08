enum E{Empty,Value{n:i64}}fn same(a:E.Empty)->E.Empty{return a;}fn main(){var a:E.Empty=E.Empty;let b:E.Empty=same(a);assert(&a .!= &b);print("enum_inline");}
