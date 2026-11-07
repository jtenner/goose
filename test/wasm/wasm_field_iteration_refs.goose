struct Row { refs: i64&[2] }
struct Holder { rows: Row&[2] }
var calls: i64 = 0;
recursive fn pick() -> i64 { calls++; return 0; }
fn main() {
    var a: i64 = 1; var b: i64 = 2; var c: i64 = 10; var d: i64 = 20;
    var first: Row = Row { refs: [a, b] }; var second: Row = Row { refs: [c, d] };
    var holder: Holder = Holder { rows: [first, second] }; var total: i64 = 0;
    for ref, i in holder.rows[pick()].refs {
        if i == 0 { holder.rows[0] .= second; }
        total += ref;
        ref += 1;
    }
    assert(calls == 1); assert(total == 21); assert(a == 2); assert(b == 2); assert(c == 10); assert(d == 21);
    print("field-refs");
}
