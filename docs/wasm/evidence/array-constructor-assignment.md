# Fresh fixed-array assignment values

Fixed and statically limited array assignment now admits exact-type array
literals, fills and defaults. The existing checked temporary-owner service
constructs the whole value in a separate Memory 0 span. It copies the image to
the captured destination only after construction completes, then restores the
temporary span. The source type must still match the stored destination type.
Stored different-layout values and general by-value array calls/results remain
guarded. String assignment is not added in this step.

The production change extends two admission checks in wasm_fixed.h. It uses
no fake frontend variables, new compiler field, runtime descriptor or new heap
object. Each active constructor needs its complete fixed image, with a minimum
one-byte reservation for an empty image. Nested assignments keep separate
reservations. Copy work follows the fixed image size; fill and default element
work uses the existing construction paths. No runtime, compiler-cost or
physical-memory measurement is claimed or required by the owner scope.

Thirty native-first O0/O2 cases pass natively and stop at the prior exact Wasm
assignment guard. Fifteen source families cover scalar and nominal elements,
fixed and limited lengths, exact defaults and fills, data fields, thin and
packed references, reads of the old target, count-zero effects, early return,
looped construction and nested replacement. The focused candidate run passes
all thirty case/optimization pairs in Node and Wasmtime, with completed-owner
checks. It also passes eight live-owner/control groups, four failure-image
groups and seven retained/accepted assignment-policy groups.

The live observer checks the actual Memory 0 top while a temporary is active,
after assignment, and after the runner's completion signal. It distinguishes
two simultaneous nested images. A validated missing-restore mutation fails the
specific live-top assertion. A constructor division failure leaves the old
permanent Memory 0 image unchanged. A target bounds failure occurs before RHS
effects or a new constructor reservation. Those failure inputs are verified
natively before their Wasm checks. Ordinary trap paths do not claim normal
completion or restoration of a trapped instance's whole stack.

Two preflight fixture errors remain preserved. The first used a nonexistent
fill function; the corrected input uses Goose array-fill syntax. Another put a
struct declaration inside a function; it was moved to file scope. Completed
valid cases from that attempt are retained, and only unfinished cases were run
in the continuation. Neither setup error is classified as a compiler defect.

The final correctness-only suite passes 2,105 groups, including all forty
complete Memory 0/data matrix cases. The native baseline passes 1,988 frontend,
970 generated-C and 1,142 TinyCC groups and all other baseline groups. All 52
exact comparisons pass; all 448 unchanged parent module pairs are identical.
The compiler SHA256 is
`757018b1b3bb91fecd9e35cd59b0870bd72756ef06360e5aa074f352a25194aa`.
All 73 source hashes and 4,565 validation input hashes match before and after
validation. Selected records are saved in the
[archive manifest](array-constructor-assignment/archive-manifest.json).
Raw evidence remains in /tmp/goose-wasm-array-constructors-20261108. This is correctness-only work, with no
timing or measurement-lease rotation.
