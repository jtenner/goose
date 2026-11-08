recursive fn make(p:i64&?)->i64&?[2]{return[p,null];}
fn main(){var a:i64=7;assert(make(null)==make(null));assert(make(a)!=make(null));print("optional_refs");}
