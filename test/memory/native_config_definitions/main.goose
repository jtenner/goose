// Explicit native --define inputs; run test/native_config_definitions.py.
// Nested outside the ordinary fixture glob. No application C helper.
import std;
import os;

let LOAD_ALIAS = build::LOAD_ORDER;
let LOAD_CHAIN = LOAD_ALIAS;
let STORE_ALIAS = build::STORE_ORDER;
let STORE_CHAIN = STORE_ALIAS;
let SUCCESS_ALIAS = build::CAS_SUCCESS;
let SUCCESS_CHAIN = SUCCESS_ALIAS;
let FAILURE_ALIAS = build::CAS_FAILURE;
let FAILURE_CHAIN = FAILURE_ALIAS;
let ADVICE_ALIAS = build::ADVICE;
let ADVICE_CHAIN = ADVICE_ALIAS;
let SIZE_ALIAS = build::MEM_BYTES;
let OFFSET_ALIAS = build::OFFSET;
let VALUE_ALIAS = build::VALUE;
let ENDIAN_ALIAS = build::BIG_ENDIAN;

fn check_atomic<T>(token: T) {
    const if build::USE_ALIAS {
        atomic_store(token, 11, STORE_CHAIN);
        assert(atomic_load(token, LOAD_CHAIN) == 11);
        let seen, exchanged = atomic_compare_exchange(token, 11, 12, SUCCESS_CHAIN, FAILURE_CHAIN);
        assert(seen == 11 && exchanged);
        let old, failed = atomic_compare_exchange(token, 11, 13, SUCCESS_CHAIN, FAILURE_CHAIN);
        assert(old == 12 && !failed && atomic_load(token, LOAD_CHAIN) == 12);
    } else {
        atomic_store(token, 11, build::STORE_ORDER);
        assert(atomic_load(token, build::LOAD_ORDER) == 11);
        let seen, exchanged = atomic_compare_exchange(token, 11, 12, build::CAS_SUCCESS, build::CAS_FAILURE);
        assert(seen == 11 && exchanged);
        let old, failed = atomic_compare_exchange(token, 11, 13, build::CAS_SUCCESS, build::CAS_FAILURE);
        assert(old == 12 && !failed && atomic_load(token, build::LOAD_ORDER) == 12);
    }
    return;
}
fn main() {
    let argv = args(); assert(argv.len == 2);
    let owner, allocated = shared_alloc(build::ALLOC_BYTES); assert(allocated);
    let data = shared_view(owner, 0, SIZE_ALIAS);
    let token32 = shared_atomic_u32(owner, 64, 0);
    let token64 = shared_atomic_u64(owner, 72, 0);
    let a = shared_borrow(data);
    // Direct integer/bool definition operands, then immutable global aliases.
    memory_write<u16>(a, build::OFFSET, build::VALUE as u16, build::BIG_ENDIAN);
    assert(memory_read<u16>(a, build::OFFSET, build::BIG_ENDIAN) == build::VALUE);
    memory_write<u16>(a, OFFSET_ALIAS + 8, VALUE_ALIAS as u16, ENDIAN_ALIAS);
    assert(memory_read<u16>(a, OFFSET_ALIAS + 8, ENDIAN_ALIAS) == VALUE_ALIAS);
    let first = if build::BIG_ENDIAN { (build::VALUE >> 8) as! u8 } else { build::VALUE as! u8 };
    assert(memory_read<u8>(a, build::OFFSET, false) == first);
    shared_release(a);
    check_atomic(token32);
    check_atomic(token64);
    var contents: u8[4096] = [0; 4096];
    assert(write_file(argv[1], contents));
    let mapped, mapped_ok = shared_map_readonly(argv[1], 4096); assert(mapped_ok);
    let view = shared_view(mapped, 0, 4096);
    const if build::USE_ALIAS {
        let supported, applied = shared_page_advice(view, 0, 4096, ADVICE_CHAIN);
        assert(!applied || supported);
    } else {
        let supported, applied = shared_page_advice(view, 0, 4096, build::ADVICE);
        assert(!applied || supported);
    }
    assert(shared_close(mapped) && shared_close(owner));
    assert(delete_file(argv[1]));
    print("native config ok ", build::USE_ALIAS, " ", build::BIG_ENDIAN);
}
