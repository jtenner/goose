var absent: i64[]&[2]? = null;
fn read(a: i64[]&[2]&) -> i64 { a[0].len }
fn main() { if absent { print(read(absent)); } print("ok"); }
