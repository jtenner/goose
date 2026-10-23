// runtime-debug: odd worker packets copy global images, including string aliases.
struct Prefix { tag: u8 }
struct Bag { tag: u8, bytes: u8[>..] }
let FIRST = "Release";
let ORDER = FIRST;
var text: u8[] = "odd";
var bytes: u8[>..] = [];
var bag = Bag { tag: 9, bytes: [] };
reusable var pool: u8[>..] = [];
reusable[] var spans: u8[>..] = [];
var generation: u8 = 0;

thread_fn worker(p: Prefix, fail: bool) {
    assert(p.tag == 7 && FIRST == "Release" && ORDER == "Release");
    assert(text == "odd" && bytes.len == generation && bag.bytes.len == generation);
    for i in bytes.len { assert(bytes[i] == 17 && bag.bytes[i] == 17); }
    assert(bag.tag == 9);
    assert(pool.len == 3 && pool.alloc_index(44) == 1);
    assert(pool[0] == 1 && pool[1] == 44 && pool[2] == 3);
    let slot = spans.alloc_slice(1);
    assert(spans.index_of(slot[0]) == 1);
    let r = text;
    r[0] = 'X';
    bytes.push(55);
    bag.bytes.push(66);
    generation = 99;
    if fail { abort("packet contained abort"); }
}
fn main() {
    pool.alloc_index(1); pool.alloc_index(2); pool.alloc_index(3); pool.free(1);
    let span = spans.alloc_slice(3);
    spans.free_slice(span[1..]);
    for n in 0..6 {
        generation = n as u8;
        for repeat in 3 {
            assert(thread_wait(thread_spawn(worker, Prefix { tag: 7 }, false)));
            assert(thread_wait(thread_spawn_contained(worker, Prefix { tag: 7 }, false)));
            var why: u8[>..] = [];
            assert(!thread_wait(thread_spawn_contained(worker, Prefix { tag: 7 }, true), why));
            assert(why.len >= 22);
            for ch, i in "packet contained abort" { assert(why[i] == ch); }
            assert(text == "odd" && bytes.len == n && bag.bytes.len == n);
            assert(generation == n as u8 && pool.len == 3 && spans.len == 3);
        }
        bytes.push(17); bag.bytes.push(17);
    }
    assert(pool.alloc_index(88) == 1);
    assert(spans.index_of(spans.alloc_slice(1)[0]) == 1);
    print("worker packet globals passed");
}
