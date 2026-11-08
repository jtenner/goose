struct S{n:i64}
recursive fn run(early:bool)->S{var s:S=-({if early{return S{n:7};}S{n:7}});return s;}
fn main(){var a:S=run(true);var b:S=run(false);assert(a.n==7);assert(b.n == -7);print("early");}
