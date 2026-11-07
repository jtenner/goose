struct Cell { value: i64 }
struct Holder { target: i64& }
struct WithCopy { first: Cell, second: i64 }
struct Text { bytes: u8[3] }
var left: Cell = Cell { value: 10 };
var right: Cell = Cell { value: 200 };
var current: Cell& = left;
var first: i64 = 30;
var second: i64 = 40;
var holder: Holder = Holder { target: first };
fn redirect() -> i64 { current .= right; return 3; }
fn redirect_field() -> i64 { holder.target .= second; return 5; }
fn change(a: Cell&) -> i64 { a.value = 77; return 9; }
fn change_text(a: Text&) -> i64 { a.bytes[0] = 90; return 1; }
fn main() {
    current.value += redirect();
    print("captured=", left.value, ",", right.value, ",", current.value);
    holder.target += redirect_field();
    print("field=", first, ",", second, ",", holder.target);
    var copied: WithCopy = WithCopy { first: left, second: change(left) };
    print("order=", copied.first.value, ",", copied.second, ",", left.value);
    var text: Text = Text { bytes: "abc" }; print(text.bytes, ",", change_text(text), ",", text.bytes);
}
