var a: i64[>..] = [1];
var b: i64[>..] = [10, 20, 30];
var selected: i64[>..]& = a;
var calls = 0;
fn choose_b() { selected .= b; }
fn current() -> i64[>..]& { calls += 1; return selected; }
fn main() {
    print("direct");
    selected .= a;
    for value in selected { print(value); selected .= b; }
    print("call");
    selected .= a;
    for value in selected { print(value); choose_b(); continue; }
    print("short");
    selected .= b;
    for value in selected { print(value); selected .= a; }
    print("once");
    selected .= a;
    for value in current() { print(value); selected .= b; }
    print(calls);
    print("alias");
    selected .= a;
    let alias .= selected;
    for value in alias { print(value); selected .= b; }
}
