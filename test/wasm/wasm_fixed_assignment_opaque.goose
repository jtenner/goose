struct S { mark: u8, word: u32, tail: u16 }
recursive fn set_value(dst: S&, src: S&) { dst = src; }
fn main() { var frame: S = S { mark: 1, word: 10, tail: 50001 }; var a: S[] = [S { mark: 2, word: 20, tail: 60002 }]; var b: S[] = [S { mark: 3, word: 30, tail: 40003 }]; set_value(frame, a[0]); assert(frame.word == 20); set_value(a[0], b[0]); assert(a[0].mark == 3); set_value(b[0], frame); assert(b[0].word == 20); set_value(frame, frame); assert(frame.tail == 60002); print("opaque"); }
