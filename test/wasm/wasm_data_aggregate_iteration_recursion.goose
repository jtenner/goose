struct S { n: i64 }
recursive fn walk(views: S[]&[4]&, depth: i64, parent: S?) -> i64 {
    var saved: i64[2] = [depth, 90 + depth]; var total: i64 = 0;
    for s in views[depth] {
        if parent {
            assert(&s .!= parent);
            assert(parent.n == s.n + 1);
        }
        assert(s.n == depth + 1); print("enter=", depth);
        if depth > 0 { total += walk(views, depth - 1, s); }
        assert(s.n == depth + 1); assert(saved[0] == depth); assert(saved[1] == 90 + depth);
        total += s.n; print("exit=", depth);
    }
    return total;
}
fn main() {
    var a: S[] = [S { n: 1 }]; var b: S[] = [S { n: 2 }];
    var c: S[] = [S { n: 3 }]; var d: S[] = [S { n: 4 }];
    var views: S[]&[4] = [a, b, c, d];
    assert(walk(views, 3, null) == 10); print("recursion");
}
