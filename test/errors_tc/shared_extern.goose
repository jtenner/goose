// error: do not cross
extern "fake_shared_api" fn foreign(v: SharedView);
fn main() { let o, ok = shared_alloc(8); foreign(shared_view(o, 0, 8)); }
