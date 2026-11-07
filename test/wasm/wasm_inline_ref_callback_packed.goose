recursive fn fixedIdentity(a: i64[2]&) -> i64[2]& { return a; }
inline fn limitedIdentity(a: i64[..3]&) -> i64[..3]& { return a; }
recursive fn relayFixed<F>(a: i64[2]&) -> i64[2]& { return F(a); }
inline fn relayLimited<F>(a: i64[..3]&) -> i64[..3]& { return F(a); }
recursive fn relayMaybeFixed<F>(a: i64[2]?) -> i64[2]? { return F(a); }
inline fn relayMaybeLimited<F>(a: i64[..3]?) -> i64[..3]? { return F(a); }
fn main() {
    var live: i64[] = [91];
    var fixed: i64[2] = [11, 22];
    var limited: i64[..3] = [33];
    var selected: i64[2]& = relayFixed(fixed, fixedIdentity);
    assert(selected .== fixed); selected[0] += 4; assert(fixed[0] == 15);
    var chosen: i64[..3]& = relayLimited(limited, limitedIdentity);
    assert(chosen .== limited); chosen.push(44);
    assert(limited.len == 2); assert(limited[0] == 33); assert(limited[1] == 44);
    var maybe: i64[2]? = null;
    var none: i64[2]? = relayMaybeFixed(maybe) { p: i64[2]? => p };
    assert(none == null); maybe .= fixed;
    var present: i64[2]? = relayMaybeFixed(maybe) { p: i64[2]? => p };
    if present { assert(present .== fixed); present[1] += 5; } else { assert(false); }
    assert(fixed[1] == 27);
    var maybeLimited: i64[..3]? = null;
    var noLimited: i64[..3]? = relayMaybeLimited(maybeLimited) { p: i64[..3]? => p };
    assert(noLimited == null); maybeLimited .= limited;
    var presentLimited: i64[..3]? = relayMaybeLimited(maybeLimited) { p: i64[..3]? => p };
    if presentLimited { assert(presentLimited .== limited); presentLimited.push(55); } else { assert(false); }
    assert(limited.len == 3); assert(limited[2] == 55);
    assert(live[0] == 91);
    print("callback-reference=ok");
}
