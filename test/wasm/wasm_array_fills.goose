var calls = 0;
var global: i16[u8] = [7; 4];
fn tick() -> i64 {
    calls++;
    var temporary: i64[] = [calls, 99];
    return temporary[0];
}
fn large() -> i64 {
    var a: i64[u16] = [tick(); 9000];
    return a[0] + a[8999];
}
fn main() {
    print("before=", large());
    var fixed: i64[3] = [tick(); 3];
    var limited: i64[..4] = [tick(); 2];
    var variable: i64[u8] = [tick(); 3];
    var grow: i64[>..] = [tick(); 3];
    var shrink: i64[>..<] = [tick(); 2];
    limited.push(11); grow.push(12); shrink.pop();
    print(fixed[0], ",", fixed[2], ",", limited.len, ",", limited[0], ",", limited[2]);
    print(variable.len, ",", variable[0], ",", variable[2], ",", grow.len, ",", grow[2], ",", grow[3]);
    print(shrink.len, ",", shrink[0], ",", calls);
    var emptyfixed: i64[0] = [tick(); 0];
    var emptylimited: i64[..3] = [tick(); 0];
    var emptyvariable: i64[] = [tick(); 0];
    var emptygrow: i64[>..] = [tick(); 0];
    print("empty=", emptyfixed.len, ",", emptylimited.len, ",", emptyvariable.len, ",", emptygrow.len, ",", calls);
    var source: i64 = 20;
    var refs: i64&[] = [source; 3];
    for &v in refs { v += 1; }
    print("refs=", source, ",", refs[0], ",", refs[2]);
    var small: i64[2] = [8, 9];
    var thin: i64[2]&[] = [small; 2];
    thin[0][0] += 2; print("thin=", thin[1][0]);
    var floats: f32[u64] = [-0.0; 2];
    var flags: bool[u16] = [true; 3];
    var bytes: u8[u8] = [255; 4];
    print("scalar=", floats[1], ",", flags[2], ",", bytes[3]);
    var largefill: i64[] = [123; 9000];
    print("growth=", largefill.len, ",", largefill[8999]);
    print("after=", large(), ",", calls, ",", global.len, ",", global[3]);
}
