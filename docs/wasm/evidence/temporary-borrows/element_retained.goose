recursive fn make()->i64[2]{return[7,8];}recursive fn borrow(p:i64&)->i64&{return p;}recursive fn read(p:i64&)->i64{return p;}fn main(){assert(read(borrow(make()[1]))==8);print("borrow_guard");}
