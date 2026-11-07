"""Native-valid array-copy target admission regressions."""
CASES = {
 'fixed-limited': 'fn main() { var a: u8[3] = [1, 2, 3]; var b: u8[..4] = a; print(b.len, ",", b[0]); }',
 'ref-fixed-limited': 'fn main() { var a: u8[3] = [1, 2, 3]; var r: u8[3]& = a; var b: u8[..4] = r; print(b.len, ",", b[0]); }',
 'limited-capacity': 'fn main() { var a: u8[..4] = [1, 2, 3]; var b: u8[..8] = a; print(b.len, ",", b[0]); }',
 'ref-limited-capacity': 'fn main() { var a: u8[..4] = [1, 2, 3]; var r: u8[..4]& = a; var b: u8[..8] = r; print(b.len, ",", b[0]); }',
 'prefix-width': 'fn main() { var a: u8[u8] = [1, 2, 3]; var b: u8[u16] = copy(a); print(b.len, ",", b[0]); }',
 'ref-prefix-width': 'fn main() { var a: u8[u8] = [1, 2, 3]; var r: u8[u8]& = a; var b: u8[u16] = copy(r); print(b.len, ",", b[0]); }',
 'varint-prefix-width': 'fn main() { var a: u8[varint] = [1, 2, 3]; var b: u8[u16] = copy(a); print(b.len, ",", b[0]); }',
 'fixed-prefix-varint': 'fn main() { var a: u8[u16] = [1, 2, 3]; var b: u8[varint] = copy(a); print(b.len, ",", b[0]); }',
 'call-layout': 'recursive fn pick(a: u8[3]&) -> u8[3]& { return a; } fn main() { var a: u8[3] = [1, 2, 3]; var b: u8[..4] = pick(a); print(b.len, ",", b[0]); }',
 'inline-call-layout': 'inline fn pick(a: u8[3]&) -> u8[3]& { return a; } fn main() { var a: u8[3] = [1, 2, 3]; var b: u8[..4] = pick(a); print(b.len, ",", b[0]); }',
 'indexed-layout': 'fn main() { var a: u8[3] = [1, 2, 3]; var refs: u8[3]&[1] = [a]; var b: u8[..4] = refs[0]; print(b.len, ",", b[0]); }',
 'inline-fixed-argument': 'inline fn first(a: u8[3]) -> u8 { return a[0]; } fn main() { var a: u8[3] = [1, 2, 3]; print(first(a)); }',
 'inline-variable-argument': 'inline fn first(a: u8[]) -> u8 { return a[0]; } fn main() { var a: u8[] = [1, 2, 3]; print(first(copy(a))); }',
}

def reason(name):
    return (b"by-value arrays need the pending destination lowering" if name.startswith("inline-") and name.endswith("-argument")
            else b"array adaptation needs the pending destination lowering")
