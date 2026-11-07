fn update(a: i64[2]&, b: i64[..3]&, value: i64&) {
    a[0] += value; b.push(a[0]);
}
fn rebind(a: i64[2]&[>..]&, value: i64[2]&) { a[0] .= value; }
fn first(a: i64[2]&) -> i64 { a[0] }
fn main() {
    var growing: i64[>..] = [3];
    var fixed: i64[2] = [10, 20];
    var limited: i64[..3] = [30];
    update(fixed, limited, growing[0]);
    var refs: i64&[2] = [fixed[0], growing[0]];
    refs[0] += 1; refs[1] += 2;
    for &v in refs { v += 10; }
    refs[1] .= fixed[1]; refs[1] += 1;
    print(fixed[0], ",", fixed[1], ",", growing[0], ",", limited[1]);
    var other: i64[2] = [40, 50];
    var owners: i64[2]&[2] = [fixed, other];
    for &a in owners { a[0] += 1; print(a[0], ",", a[1]); }
    var small_refs: i64&[..3] = [];
    small_refs.push(fixed[0]); small_refs.push(growing[0]);
    for &v in small_refs { v += 1; }
    print(fixed[0], ",", growing[0], ",", small_refs.pop());
    var dynamic_owners: i64[2]&[>..] = [fixed];
    rebind(dynamic_owners, other); print("selected=", first(dynamic_owners[0]));
    var current: i64[2]& = fixed;
    for &v, i in current { if i == 0 { current .= other; } v += 1; }
    print(fixed[0], ",", other[1]);
}
