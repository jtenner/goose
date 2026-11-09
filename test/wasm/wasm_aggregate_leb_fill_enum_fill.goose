enum Choice { A { x:i64 }, B { y:u8 } }
fn main(){var a:Choice[varint]=[Choice.A{x:23};2];assert(a.len==2);match a[1]{A p=>assert(p.x==23),B p=>assert(false)}print("enum_fill");}
