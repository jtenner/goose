recursive fn relayFixed<F>(a: i64[2]&) -> i64[2]& { return F(a); }
inline fn relayLimited<F>(a: i64[..3]&) -> i64[..3]& { return F(a); }
fn main() {
    var live: i64[] = [91];
    var fixed: i64[2] = [11, 22];
    var limited: i64[..3] = [33];
    var selected: i64[2]& = relayFixed(fixed) { p: i64[2]& => &p };
    assert(selected .== fixed); selected[0] += 4; assert(fixed[0] == 15);
    var chosen: i64[..3]& = relayLimited(limited) { p: i64[..3]& => &p };
    assert(chosen .== limited); chosen.push(44);
    assert(limited.len == 2); assert(limited[0] == 33); assert(limited[1] == 44);
    assert(live[0] == 91);
    print("callback-reference=ok");
}
