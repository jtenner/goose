struct Link { before: u8, target: i64[2]&, limited: i64[..3]&, maybe: i64[2]?, after: u32 }
var globalarray: i64[2] = [1, 2];
var globalref: i64[2]& = globalarray;
var globalmaybe: i64[2]? = null;
recursive fn fixedref(a: i64[2]&) -> i64[2]& { return a; }
recursive fn limitedref(a: i64[..3]&) -> i64[..3]& { return a; }
recursive fn optionalref(a: i64[2]?, keep: bool) -> i64[2]? { if keep { return a; } return null; }
recursive fn choose(a: i64[2]&, b: i64[2]&, first: bool) -> i64[2]& {
    if first { return a; } return b;
}
inline fn inlineref(a: i64[2]&) -> i64[2]& { return a; }
fn invoke<F>(a: i64[2]&) { F(a); }
fn change(a: u8[3]&) -> i64 { a[0] = 88; return 0; }
struct HeaderLink { before: u8, target: i64[>..]&, after: u16 }
recursive fn headerref(a: i64[>..]&) -> i64[>..]& { return a; }
fn main() {
    var fixed: i64[2] = [10, 20]; var other: i64[2] = [30, 40];
    var limited: i64[..3] = [50];
    var link: Link = Link { before: 7, target: fixed, limited: limited, after: 4000000000 };
    assert(link.before == 7); assert(link.after == 4000000000); assert(link.maybe == null);
    link.target .= other; link.limited.push(51); link.maybe .= fixed;
    assert(link.target .== other); assert(link.limited.len == 2); assert(link.limited[1] == 51);
    var held: i64[2]? = link.maybe; if held { assert(held[1] == 20); }
    var saved: Link = copy(link); var links: Link[2] = [link, saved];
    links[0].target .= fixed; assert(links[0].target .== fixed); assert(links[1].target .== other);
    assert(links[0].after == 4000000000); assert(links[1].before == 7);
    var refs: i64[2]&[3] = [fixed, other, fixed];
    refs[1] .= fixed; assert(refs[1] .== fixed); assert(refs[2] .== fixed);
    var result: i64[2]& = choose(fixedref(fixed), inlineref(other), false);
    assert(result .== other); result[0] += 1; assert(other[0] == 31);
    var optional: i64[2]? = optionalref(fixed, true); assert(optional .== fixed);
    optional .= optionalref(other, false); assert(optional == null);
    limitedref(limited).push(52); assert(limited.len == 3); assert(limited[2] == 52);
    invoke(other) { p: i64[2]& => assert(p .== other); p[1] += 3; };
    assert(other[1] == 43);
    globalref[0] += 4; globalmaybe .= globalarray;
    if globalmaybe { assert(globalmaybe[0] == 5); }
    assert(globalref .== globalarray);
    var text: u8[3] = [65, 66, 67];
    print("bytes=", text, "|", change(text), "|", text);
    var byteview: u8[3]? = null; print("optional=", byteview);
    byteview .= text; print("bytes=", byteview);
    var values: i64[] = [99];
    var owners: i64[2]&[] = [fixed, other]; owners[0] .= other;
    assert(owners[0] .== other); assert(owners[1][1] == 43);
    var growing: i64[>..] = [7];
    var header: HeaderLink = HeaderLink { before: 9, target: growing, after: 60000 };
    header.target.push(8); var copiedheader: HeaderLink = copy(header); copiedheader.target.push(9);
    var returned: i64[>..]& = headerref(growing); returned.push(10);
    assert(growing.len == 4); assert(growing[3] == 10);
    assert(header.before == 9); assert(header.after == 60000); assert(copiedheader.after == 60000);
    assert(values[0] == 99);
    print("ABI=ok");
}
