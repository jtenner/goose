struct vector { value: i64 }

fn align(x: i64) -> i64 { x + 1 }

fn main() {
    let v: vector = vector { value: 3 };
    align(4);
    print(v.value, " ", align(v.value));
}
