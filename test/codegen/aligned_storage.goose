// no-jit: align(N) is deliberately rejected by the TinyCC backend.

struct LaneBlock {
    tag: u8,
    align(16) lanes: u32[4],
}

struct Outer {
    prefix: u8,
    payload: LaneBlock,
}

align(32) var global: Outer = Outer {
    prefix: 1,
    payload: LaneBlock { tag: 2, lanes: [3, 4, 5, 6] },
};

fn main() {
    align(64) var values: Outer[2] = [global, global];
    values[1].payload.lanes[3] = 9;
    print(values[0].prefix, " ", values[1].payload.tag, " ", values[1].payload.lanes[3]);
}
