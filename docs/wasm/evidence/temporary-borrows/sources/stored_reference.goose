struct S{p:i64&}recursive fn make(p:i64&)->S{return S{p:p};}recursive fn read(p:i64&)->i64{return p;}fn main(){var a:i64[]=[41];assert(read(make(a[0]).p)==41);print("stored_reference");}
