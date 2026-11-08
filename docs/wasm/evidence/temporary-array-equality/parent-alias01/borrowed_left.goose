var values:i64[2]=[7,8];var lc:i64=0;var rc:i64=0;
recursive fn left()->i64[2]&{lc++;return values;}
recursive fn right()->i64[2]{rc++;values[0]=9;return[7,8];}
fn main(){assert(left()==right());assert(lc==1);assert(rc==1);assert(values[0]==9);print("borrowed_left");}
