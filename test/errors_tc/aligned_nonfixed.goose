// error: aligned struct fields require fixed packed storage
struct Bad {
    align(16) xs: u8[],
}

fn main() { let x: Bad; }
