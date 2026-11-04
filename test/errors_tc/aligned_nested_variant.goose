struct Aligned { tag: u8, align(32) value: u32 }

enum Message { Data { payload: Aligned }, Empty }

// error: aligned types are unsupported in enum payloads
fn main() { let message: Message; }
