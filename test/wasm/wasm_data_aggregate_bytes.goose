struct Word { bytes: u8[3] }
recursive fn mutate(rows: Word[]&) -> i64 { rows[0].bytes[0] = 120; return 7; }
fn main() {
    var rows: Word[] = [Word { bytes: "abc" }];
    print(rows[0].bytes, "=", mutate(rows));
    assert(rows[0].bytes[0] == 120);
    var present: u8[3]? = rows[0].bytes;
    var absent: u8[3]? = null;
    print(present); print(absent);
}
