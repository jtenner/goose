namespace local {
    struct SharedOwner { value: i64 }
    fn get() -> i64 { let x = SharedOwner { value: 42 }; x.value }
}
fn identity<SharedOwner>(x: SharedOwner) -> SharedOwner { x }
fn main() { assert(identity(7) == 7); assert(local::get() == 42); print("native names ok"); }
