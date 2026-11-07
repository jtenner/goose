fn rebind(a: i64[2]?[>..]&, value: i64[2]?) {
    a[0] .= value; a[1] .= null;
}
fn main() {
    var a: i64[2] = [1, 2];
    var direct: i64[2]?[..2] = [null, a];
    for owner in direct {
        if owner { print(owner[0]); } else { print("null"); }
    }
    var indirect: i64[2]?[>..] = [null, a];
    rebind(indirect, a);
    for owner in indirect {
        if owner { print(owner[1]); } else { print("null"); }
    }
}
