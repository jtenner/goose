fn first<T>(a: const T[>..]&) -> T { a[0] }
fn second<T>(a: const T[>..]&) -> T { a[1] }
fn set_value<T>(p: T&, value: T) { p = value; }
fn main() {
{
var a: i8[>..] = [127];
a.push(-1);
let r = &a[0];
a[0] += 1;
print("i8:", first(a), ",", second(a), ",", r);
set_value(r, 127);
print(a[0]);
}
{
var a: i16[>..] = [32767];
a.push(-1);
let r = &a[0];
a[0] += 1;
print("i16:", first(a), ",", second(a), ",", r);
set_value(r, 32767);
print(a[0]);
}
{
var a: i32[>..] = [2147483647];
a.push(-1);
let r = &a[0];
a[0] += 1;
print("i32:", first(a), ",", second(a), ",", r);
set_value(r, 2147483647);
print(a[0]);
}
{
var a: i64[>..] = [9223372036854775807];
a.push(-1);
let r = &a[0];
a[0] += 1;
print("i64:", first(a), ",", second(a), ",", r);
set_value(r, 9223372036854775807);
print(a[0]);
}
{
var a: u8[>..] = [255];
a.push(7);
let r = &a[0];
a[0] += 1;
print("u8:", first(a), ",", second(a), ",", r);
set_value(r, 255);
print(a[0]);
}
{
var a: u16[>..] = [65535];
a.push(7);
let r = &a[0];
a[0] += 1;
print("u16:", first(a), ",", second(a), ",", r);
set_value(r, 65535);
print(a[0]);
}
{
var a: u32[>..] = [4294967295];
a.push(7);
let r = &a[0];
a[0] += 1;
print("u32:", first(a), ",", second(a), ",", r);
set_value(r, 4294967295);
print(a[0]);
}
{
var a: u64[>..] = [18446744073709551615];
a.push(7);
let r = &a[0];
a[0] += 1;
print("u64:", first(a), ",", second(a), ",", r);
set_value(r, 18446744073709551615);
print(a[0]);
}
{
var a: f32[>..] = [0.0];
a.push(1.25);
let r = &a[0];
a[0] += 0.5;
print("f32:", first(a), ",", second(a), ",", r);
set_value(r, -0.0);
print(a[0]);
}
{
var a: f64[>..] = [0.0];
a.push(1.25);
let r = &a[0];
a[0] += 0.5;
print("f64:", first(a), ",", second(a), ",", r);
set_value(r, -0.0);
print(a[0]);
}
{
var a: bool[>..] = [true];
a.push(true);
let r = &a[0];
a[0] = false;
print("bool:", first(a), ",", second(a), ",", r);
set_value(r, true);
print(a[0]);
}
}
