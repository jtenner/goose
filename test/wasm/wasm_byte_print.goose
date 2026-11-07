fn change(a: u8[]&) -> i64 { a[0] = 88; print("nested"); return 0; }
recursive fn early(b: bool) -> i64 {
    var a: u8[] = [65, 66];
    defer { print("defer-exit"); }
    print("unused=", a, if b { return 7; } else { 8 });
    return 9;
}
fn inline_early(b: bool) -> i64 {
    var a: u8[] = [67, 68];
    print("unused-inline=", a, if b { return 10; } else { 11 });
    return 12;
}
fn grow(a: u8[>..]&) -> i64 { for i in 70000 { a.push(120); } return a.len; }
fn main() {
    var a: u8[] = [97, 98, 99];
    print("capture=", a, "|", change(a), "|", a);
    print("after-exit=", early(true));
    print("after-normal=", early(false));
    print("after-inline=", inline_early(true));
    print("after-inline-normal=", inline_early(false));
    var optional: u8[]? = null;
    print("optional=", optional); optional .= a;
    print("optional=", optional); optional .= null; print("optional=", optional);
    var fixed: u8[3] = [65, 0, 66];
    var pointer: u8[3]? = null;
    print("fixed=", fixed, ",", pointer); pointer .= fixed;
    print("fixed=", pointer); pointer .= null; print("fixed=", pointer);
    var limited: u8[..5] = [100, 101];
    var builder: u8[>..] = [71];
    print("limited=", limited);
    print("growth=", builder, "|", grow(builder), "|", builder.len);
    var empty: u8[] = []; print("empty=", empty, "!");
    for i in 3 {
        var text: u8[] = [80, 81];
        defer { print("loop-exit=", i); }
        print("unused-loop=", text, if i == 0 { continue; } else if i == 1 { break; } else { 4 });
    }
    print("done-bytes");
}
