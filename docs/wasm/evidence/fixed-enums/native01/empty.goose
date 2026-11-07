enum Z { Empty, Blank {}, Pad { pad 3 } }
fn main() {
 var a: Z.Empty = Z.Empty {}; var b: Z.Empty = default<Z.Empty>(); assert(&a .!= &b);
 var blank: Z.Blank = Z.Blank {}; var copied: Z.Blank = copy(blank); assert(&blank .!= &copied);
 var tagged: Z = Z.Empty; var pad: Z.Pad = Z.Pad {}; var other: Z.Pad = copy(pad); assert(&pad .!= &other);
 match tagged { Empty => print("empty"), Blank, Pad => assert(false) }
 match tagged { const for <N, V> in variants<Z> { V payload => { var own: V = copy(payload); assert(&own .!= &payload); print(N); }, } }
}
