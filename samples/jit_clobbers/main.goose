// Native --define configuration and actual register ownership validation.
// See README.md in this directory. No C sidecar or application runtime helper.
import std;
import os;

struct Emitter {
    const if build::CHECK_REGISTER_CLOBBERS {
        register_owners: u32[2], // eax, ecx; zero means free
    } else {},
    code: u8[>..],
}

fn validate_register_ownership(e: Emitter&, reg: i64, expected: u32) {
    const if build::CHECK_REGISTER_CLOBBERS {
        if e.register_owners[reg] != expected { abort("REGISTER_CLOBBER_SENTINEL"); }
    }
}
fn claim_register(e: Emitter&, reg: i64, owner: u32) {
    const if build::CHECK_REGISTER_CLOBBERS {
        validate_register_ownership(e, reg, 0);
        e.register_owners[reg] = owner;
    }
}
fn release_register(e: Emitter&, reg: i64, owner: u32) {
    const if build::CHECK_REGISTER_CLOBBERS {
        validate_register_ownership(e, reg, owner);
        e.register_owners[reg] = 0;
    }
}
fn constant(e: Emitter&, value: u32, owner: u32) {
    const if build::CHECK_REGISTER_CLOBBERS { claim_register(e, 0, owner); }
    e.code.push(0xb8); // mov eax, imm32
    for shift in 4 { e.code.push((value >> (shift * 8)) as! u8); }
    e.code.push(0x50); // push rax: materialize the Wasm stack value
    const if build::CHECK_REGISTER_CLOBBERS { release_register(e, 0, owner); }
}
fn add(e: Emitter&) {
    const if build::CHECK_REGISTER_CLOBBERS {
        claim_register(e, 1, 2);
        claim_register(e, 0, 1);
        validate_register_ownership(e, 0, 1);
        validate_register_ownership(e, 1, 2);
    }
    e.code.append([0x59, 0x58, 0x01, 0xc8, 0x50]); // pop rcx; pop rax; add eax,ecx; push rax
    const if build::CHECK_REGISTER_CLOBBERS {
        release_register(e, 0, 1);
        release_register(e, 1, 2);
    }
}
fn main() {
    var e = Emitter {
        const if build::CHECK_REGISTER_CLOBBERS { register_owners: [0, 0], } else {},
        code: [],
    };
    const if build::CHECK_REGISTER_CLOBBERS || build::ENABLE_JIT_ASSERTIONS {
        let argv = args();
        const if build::CHECK_REGISTER_CLOBBERS {
            if argv.len > 1 && argv[1] == "clobber" {
                claim_register(e, 0, 99); // live eax, overwritten by constant()
            }
        }
        const if build::ENABLE_JIT_ASSERTIONS {
            if argv.len > 1 && argv[1] == "assertion" { abort("JIT_ASSERTION_SENTINEL"); }
        }
    }
    constant(e, 7, 1);
    constant(e, 11, 2);
    add(e);
    e.code.append([0x58, 0xc3]); // pop rax; ret
    let hex = "0123456789abcdef";
    var text: u8[>..] = [];
    for b in e.code { text.push(hex[b >> 4]); text.push(hex[b & 15]); }
    print(text);
}
