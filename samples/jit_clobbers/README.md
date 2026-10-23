# Conditional register ownership checks

```sh
goose build --define CHECK_REGISTER_CLOBBERS=true \
  --define ENABLE_JIT_ASSERTIONS=true samples/jit_clobbers/main.goose -o /tmp/clobbers
/tmp/clobbers
/tmp/clobbers clobber   # fails: overwrites a register with a live owner
/tmp/clobbers assertion # fails: separately configured JIT assertion
python3 test/jit_clobbers.py /path/to/goose
```

Set both definitions to `false` for production output. These are typed native
Goose definitions, not C preprocessor macros. `const if` selects struct fields,
constructor entries and function statements. With tracking enabled, the
emitter records ownership of eax/ecx and verifies each acquisition, use and
release. The injected `clobber` preserves a live eax value before a constant
emission tries to take eax again, producing an ownership failure. This
application logic is what detects a clobber; compiler branch removal alone
would not demonstrate ownership tracking.

Both configurations emit identical x86-64 bytes for `7 + 11`. Like the parallel
Wasm example, this example produces bytes without calling executable memory.
Acceptance builds all four flag combinations at Goose `-O0` and `-O2`, checks
success bytes and actual injected failures, and inspects generated C for
absence of fields, validation functions and diagnostic data when disabled.
It also checks objdump function symbols/disassembly when objdump is available.
Compiler inlining levels and native C optimization are separate settings;
benchmark preparation additionally builds C with explicit `-O0` and `-O2`.
