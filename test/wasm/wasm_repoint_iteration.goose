var a: i64[>..] = [1];
var b: i64[>..] = [10, 20, 30];
var selected: i64[>..]& = a;
fn choose_b() { selected .= b; }
fn main() {
    for value in selected {
        print(value);
        choose_b();
        continue;
    }
}
