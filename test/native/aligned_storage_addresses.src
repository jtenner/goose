// Native-only address/layout probe: TinyCC deliberately rejects align(N).
extern fn mod64(p: u32&) -> u64;

struct Block { tag: u8, align(64) value: u32 }
struct Nested { prefix: u8, payload: Block }

var before: u8 = 1;
align(64) var global: u32 = 2;

thread_fn worker() { print(mod64(global), " "); }
fn pass(x: Nested) -> Nested { return x; }
fn assert_zero_padding(x: Nested) {
    let wrapped = [x];
    let raw = bytes_of(wrapped);
    assert(raw.len == 192);
    for i in 1..64 { assert(raw[i] == 0); }
    for i in 65..128 { assert(raw[i] == 0); }
    for i in 132..192 { assert(raw[i] == 0); }
}

fn main() {
    let x = Nested { prefix: 3, payload: Block { tag: 4, value: 5 } };
    let values: Nested[2] = [x, pass(x)];
    assert_zero_padding(x);
    assert_zero_padding(values[0]);
    assert_zero_padding(values[1]);
    print(mod64(global), " ", mod64(x.payload.value), " ",
          mod64(values[0].payload.value), " ", mod64(values[1].payload.value), " ");
    assert(thread_wait(thread_spawn(worker)));
}
