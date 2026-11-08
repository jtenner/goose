struct S{link:i64&}
recursive fn get(p:S)->i64&{return p.link;}
fn main(){var data:i64[]=[7];var s:S=S{link:data[0]};var link:i64&=get(s);link=9;assert(data[0]==9);assert(link .== &data[0]);print("reference_result");}
