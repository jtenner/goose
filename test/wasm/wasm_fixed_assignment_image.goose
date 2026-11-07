enum E { Big { n: i64 }, Small { n: u8 }, Empty }
fn main() {
    var a: E = E.Big { n: 1000 }; var b: E = E.Small { n: 7 }; var c: E = E.Empty;
    print("seed"); a = b; print("copied"); b = c; print("emptied");
}
