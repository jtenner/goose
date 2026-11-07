var selected: i64[>..]? = null;
var shrinkable: i64[>..<]? = null;
fn append_one(a: i64[>..]&) -> i64& { return a.push(1); }
fn last(a: i64[>..<]&) -> i64 { return a.pop(); }
fn clear(a: i64[>..<]&) { a.clear(); }
fn length(a: const i64[>..<]&) -> i64 { return a.len; }
fn main() {
    if selected { print(append_one(selected)); }
    if shrinkable { print(last(shrinkable), length(shrinkable)); clear(shrinkable); }
    print("ok");
}
