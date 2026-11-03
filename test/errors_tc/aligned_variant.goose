// error: align is supported on struct fields, not variant payloads
enum Bad {
    Item {
        align(16) x: u32,
    },
}

fn main() { let x: Bad; }
