fn probe(tag: i64) -> i64 {
    var own: i64[..] = [tag, tag + 1];
    print("call=", own[1]);
    return own[0];
}
fn finish(early: bool) -> i64 {
    var a: i64[..] = [10];
    defer {
        var temp: i64[..] = [30];
        print("outer=", a[0], ",", temp[0]);
        print("outer-call=", probe(40));
    }
    {
        var b: i64[..] = [20];
        defer {
            var temp: i64[..] = [50];
            print("inner=", b[0], ",", temp[0]);
            print("inner-call=", probe(60));
        }
        if early { return a[0] + b[0]; }
        print("normal=", a[0] + b[0]);
    }
    return a[0];
}
fn main() {
    print("ret=", finish(true));
    {
        var live: i64[..] = [90];
        print("ret=", finish(false));
        print("live=", live[0]);
    }
    for i in 3 {
        var a: i64[..] = [i];
        defer {
            var temp: i64[..] = [100 + i];
            print("loop=", a[0], ",", temp[0]);
            print("loop-call=", probe(200 + i));
        }
        if i == 0 { continue; }
        if i == 1 { break; }
    }
    print("done");
}
