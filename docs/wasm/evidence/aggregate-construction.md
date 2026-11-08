# Fixed aggregate array fills and defaults

Fixed and statically limited arrays of positive fixed structs, enums and
variants now support fills and defaults. This uses the existing checked fresh
span and temporary-owner services. It adds no runtime descriptor or source
variable. A fill constructs one complete element image before copying it,
including a count-zero fill. A fixed-array default constructs each element
separately. An empty fixed or limited default evaluates no element initializer.

Each bounded copy uses the stored element stride and the actual destination
memory identity. Array fields in fresh data rows use the same path. The count,
capacity, prefix and complete fresh image are checked before emission. Nested
loops use distinct locals. Source references remain shallow copies. Return,
break, continue and defers use the existing ordered cleanup scopes.

Native-first evidence contains 46 O0/O2 cases that passed natively and failed
at the exact prior fill/default Wasm guard. All pass with the repaired compiler
in Node and Wasmtime. Cases include per-element side effects, fill-once and
zero-count effects, nested fills/defaults, active enum values, shallow reference
identity, one/two/four-byte count prefixes, memory growth, deferred allocation
on exit and fresh data spans at different call depths. Saved code confirms the
call-depth case uses the dynamic copy-from-frame dispatcher. An attempted
live nonfixed array across recursion was rejected by the language; it is an
invalid fixture, not runtime or Wasm coverage.

The host checks live frame tops at element evaluation and operation completion.
A copied full Memory 0 model checks a guarded packed limited array before and
after construction. The host seeds valid reserved payload bytes, then models
all active and inactive stored-image writes. Validated short, long, omitted and
wrong-stride copies fail at the specific image assertion. There are thirty
owner/image/control groups. Constructor padding is not required to match native
uninitialized bytes.

The focused read-only review found no confirmed production defect. Its source
hashes match the final compiler source. The owner then corrected a control
parser that assumed the whole function had one stride operation. The later
array-read assertion has another valid stride operation. The failed parser and
raw evidence remain unchanged; the corrected parser targets only the fill loop.
Additional boundary fixtures and owner assertions were added after the review.
No second review coverage is claimed for those test-only additions.

The full correctness-only suite passes 1,824 groups, including all forty
complete Memory 0/data matrix cases. The native baseline passes 1,916 frontend
groups, 934 generated-C groups, 1,106 TinyCC groups and all other baseline groups.
All 52 exact comparisons pass; 360 unchanged-source parent modules are
byte-identical. The final compiler SHA256 is
`7c0565cb9c7f1f5f7cda20e924e34bc9fbefdfe34ae02c71e718a6021b1dac7d`.
Source, test and compiler hashes match before and after validation. Selected
records are in the [archive manifest](aggregate-construction/archive-manifest.json).

Raw records are retained under
`/tmp/goose-wasm-aggregate-construction-20261107`. This is correctness-only work.
No timing, measurement lease or performance acceptance gate is used. Each fill
copies its requested elements; each default executes its element defaults and
uses one temporary at a time. These are required value-construction steps, not
runtime or physical-memory measurements.

Data-array fills, zero-stride aggregate elements, whole-array assignment,
layout adaptation, push/pop and general aggregate arguments/results remain
separate compilation work.

A later conversion regression found that a fixed default built into a wider
limited destination lost its source count. This checkpoint's exact-layout
checks did not cover that conversion. The failure and repair are recorded in
[array assignment and default-count evidence](array-assignment.md).
