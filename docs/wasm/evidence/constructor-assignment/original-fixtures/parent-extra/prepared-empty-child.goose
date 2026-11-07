enum E { Value { n: i64 }, Empty }
struct H { mark: u8, empty: E.Empty }
recursive fn stamp() -> u8 { print("seed"); return 7; }
fn main() { var target: H = H { mark: 1, empty: E.Empty }; target = H { mark: stamp(), empty: E.Empty }; assert(target.mark == 7); print("commit"); }
