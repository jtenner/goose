struct Row { numbers: i64[2] }
fn main() {
    var first: Row = Row { numbers: [1, 2] }; var second: Row = Row { numbers: [10, 20] };
    var current: Row& = first; var total: i64 = 0;
    for number, i in current.numbers { if i == 0 { current .= second; } total += number; }
    assert(total == 21); print("field-root");
}
