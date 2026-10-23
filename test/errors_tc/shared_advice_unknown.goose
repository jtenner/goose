// error: unknown page advice
fn main() { let o, ok = shared_alloc(64); shared_page_advice(shared_view(o, 0, 64), 0, 64, "DiscardLiveBytes"); }
