// dump-runtime: deferred const-if branches run at scope exit.
fn main() {
    var value = 1;
    defer const if true { print("true ", value); } else { missing(); }
    defer const if false { missing(); } else { print("false ", value); }
    defer const if false { missing(); }
        else if true { print("else if ", value); }
        else { missing(); }
    defer const if false { missing(); }
        else const if false { missing(); }
        else { print("else const if ", value); }
    defer const if false { missing(); }
    value = 2;
    print("body");
}
