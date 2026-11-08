struct S{x:i8,y:i64,z:i16[2]}
recursive fn neg(p:S&)->S{return -p;}
fn main(){var rows:S[]=[S{x:1,y:2,z:[3,-4]},S{x:-5,y:6,z:[7,8]}];var s:S=neg(rows[1]);assert(s.x==5);assert(s.y == -6);assert(s.z[0] == -7);var out:S[]=[-rows[0],-s];assert(out[0].x == -1);assert(out[0].z[1]==4);assert(out[1].x == -5);assert(out[1].z[1]==8);assert(rows[0].x==1);print("data");}
