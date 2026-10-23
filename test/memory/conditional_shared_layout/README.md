# Conditional layout and native sharing integration

This fixture combines the features in one program. It is nested outside the
ordinary fixture glob because it requires explicit configuration and its own
native compiler/sanitizer matrix:

```sh
python3 test/conditional_shared_layout.py /path/to/integrated/goose \
  --report /tmp/conditional-shared.json
```

The default runs DEBUG false/true × Goose O0/O2 × runtime release/debug
(`--debug`) × native C O0/O2 × every available GCC/Clang. With both compilers
this is 32 native configurations, all built with `-fsanitize=alignment` and
`-fno-sanitize-recover=all`. There is no alignment suppression. On Linux with
a Conda Clang in PATH, GCC additionally uses `-B/usr/bin/` to keep system GCC's
sanitizer runtime with the system linker. `--cc /path/to/clang` selects one
compiler; multiple `--cc` options select several. The JSON report records
identities and exact flags. `--compile-only` builds/inspects and performs
compiler rejection tests, but executes no programs and proves no runtime
safety. Use it while the packed-capability runtime fix is under review.

`Header` is packed: `{a:u32,c:u32}` is 8 bytes with `c` at 4; adding the selected
`debug:u64` field gives 16 bytes with `c` at 12. Live private arrays provide
`bytes_of`, selected constructors and `fields<T>` reflection check field order.
The parent explicitly copies only this Header's bytes into owned shared
storage. The worker receives authorized views, borrows bounded input and a
disjoint result range, reads the selected `c`, updates the result and publishes
with Release. The parent observes with Acquire, checks that the private
original is unchanged, joins and closes.

The application-visible wire envelope is six little-endian u32 values:
magic 0x47434853, version 1, layout ID 0x48440000+Header byte size, Header byte
size, known `c` offset, and reserved 0; then the raw packed Header bytes. This
fixture targets native little-endian Linux. The worker validates all envelope
fields and the exact mapped length before accessing the payload. Both binaries
produce actual files; each accepts its own format and rejects the other
configuration, plus independently corrupted magic/version/ID/size/offset and
reserved bytes. The explicit signature is an application protocol, not a
compiler type hash. Different configurations are NOT automatically ABI
compatible; raw private bytes do not acquire endian or schema conversion.

Private `Packed32`/`Packed64` wrappers put a conditional native capability
immediately after a u8. Selected constructors, copies, function returns and
actual atomic operations exercise that packed representation. The worker's
packed argument packet also deliberately starts with a u8 before capabilities.
The actual atomic cells remain aligned at owner offsets 104 (u32) and 112 (u64).
A capability's representation is NOT the 4/8-byte cell. Active capability
structs cannot use bytes_of/to_bytes/from_bytes; 16 compiler rejection checks
also verify absent-field access and blocked forging. False configurations
have no capability field or field metadata; their private wrappers serialize
as two ordinary tag bytes. Separate contained workers request truly misaligned
cells (u32 offset 1/u64 offset 4) and must report the alignment error safely.
No application C helper participates.
