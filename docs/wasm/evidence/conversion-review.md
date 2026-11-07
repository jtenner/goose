# Scalar conversion review

A separate read-only GPT-6.1-Sol worker reviewed the candidate against
f3d137b42275750419432eecef390e5f9c0180aa and native gs_f2iwrap. It found no
confirmed defect. It checked exact signed endpoints, ordered NaN comparisons,
f32 promotion, normalization after conversion, Wasm opcodes/types, lazy function
registration, stable existing function indices, and vector-reference lifetime.
It ran no builds, tests, or timings.

The review noted coverage gaps for first registration in global initialization,
unused-helper byte equality, and bounded f32/unsigned casts. The parent added
wasm_conversion_global.goose and the bounded conversion cases, and compared the
741-byte scalar module against the retained f3 module byte for byte. The updated
Debug and Release suites passed 78 checks, and the full native Release suite
passed. Performance evidence is recorded separately in the granted comparison.

The pre-change host-boundary test failed specifically because an in-range
conversion invoked float_to_int_v1. The candidate uses one shared helper for
[-2^63, 2^63); all other values keep the original wrapping import. Its helper
is emitted only when needed. There is no new guest heap allocation or explicit
host BigInt operation in the in-range path. Performance claims require the
separate granted comparison run; passing functional tests alone is not a speed
measurement.
