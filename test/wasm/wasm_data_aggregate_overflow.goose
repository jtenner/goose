struct Row { value: u32 }
var rows: Row[] = [Row { value: 11 }];
fn main() {
    print("ready");
    var copied: Row[] = copy(rows);
    assert(copied.len == 1); assert(copied[0].value == 11);
    print("done");
}
