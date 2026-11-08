struct S{n:i64}
recursive fn make()->S[2]{return[S{n:7},S{n:8}];}
recursive fn index()->i64{var scratch:i64[2]=[99,100];return scratch[0]-98;}
fn main(){assert(make()[index()].n==8);print("array_nominal_field");}
