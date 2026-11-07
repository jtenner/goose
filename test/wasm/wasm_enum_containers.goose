enum Link { Item { mark: u8, target: i64&, after: u16 }, None }
fn main() {
 var x: i64[] = [10]; var y: i64[] = [20];
 var a: Link = Link.Item { mark: 1, target: x[0], after: 60000 }; var b: Link = Link.Item { mark: 2, target: y[0], after: 65000 };
 var links: Link&[] = [a, b];
 match links[0] { Item p => { links[0] .= b; x[0] += 3; assert(p.mark == 1); assert(p.target == 13); assert(p.after == 60000); }, None => assert(false) }
 var copyOfB: Link = copy(links[0]); y[0] += 4;
 match copyOfB { Item p => { assert(p.mark == 2); assert(p.target == 24); assert(p.after == 65000); }, None => assert(false) }
 var f: Link&[2] = [a, b]; var l: Link&[..3] = [a]; var r: Link&[..] = [..3]; var u: Link&[varint] = [a, b]; var g: Link&[>..] = [a]; var s: Link&[>..<] = [a];
 l.push(b); r.push(b); g.push(b); s.push(b); var popped: Link& = s.pop(); assert(popped .== b); s.push(a); s.pop();
 var cf: Link&[2] = copy(f); cf[0] .= b; assert(f[0] .== a); assert(cf[0] .== b);
 for &e in g { match e { Item p => { assert(p.target >= 13); }, None => assert(false) } }
 match u[1] { Item p => assert(p.target == 24), None => assert(false) }
 match r[0] { Item p => assert(p.mark == 2), None => assert(false) }
 assert(x[0] == 13); print("packed=", l.len, ",", r.len, ",", g.len, ",", s.len);
}
