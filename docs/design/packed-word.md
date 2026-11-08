# `packed word`: named views of one integer (v1)

Status: implemented on `feat/packed-word` (u8/u16/u32/u64 backings). Validation and
environment-blocked tests are recorded in the [implementation report](../evidence/packed-word-validation.md).
Original source observations refer to commit
`f22a70de6b63dc5ae5d3fc2b98d122c354a11235`; line references are to that revision.

Owner scope decision — **2026-10-31 23:51 ET**: v1 backings are u8, u16,
u32 and u64 only. u128 and all general 128-bit scalar work are deferred to a
later round driven by a concrete two-word need. Fields and carriers cap at
64 bits. A u128 backing is rejected explicitly, never lowered as an aggregate.
This decision supersedes the earlier five-backing implementation authorization;
all other approved semantics remain unchanged.

## 1. Scope and cost model

A packed word is a nominal value whose entire representation is one unsigned
integer. Its fields describe bit views, not separately addressable storage.
A field read extracts bits; a field assignment replaces bits in that integer.
There is no allocation, object header, hidden pointer, or per-value metadata.
This is a fork-only compile-time layout feature, alongside `const if`.

```goose
enum ObjectKind { Object, Array }
packed word ObjectHeader : u64 {
    marked: bool,
    age: u2,
    kind: ObjectKind,
    size_class: u6,
    forwarded: bool,
    _: u21,
    type_id: u32,
}
```

Here the offsets are 0, 1, 3, 4, 10, 11, and 32; the widths are
1, 2, 1, 6, 1, 21, and 32. This example fills exactly 64 bits **because this
ObjectKind has two variants**. With three variants its width becomes two and
this particular declaration overflows; the author must reduce the reserved
region. Enum changes can change a layout and must never silently truncate it.

Backings are exactly `u8`, `u16`, `u32`, and `u64`. An empty declaration
still occupies its backing width. Wider records compose ordinary structs of
packed words. There are no unbounded packed blobs or arbitrary backing widths.

The lowering contract is scalar end to end: a u64 packed word local,
parameter, result, copy, equality, and field operation uses the u64 value
path. Field syntax must not itself force an address, a Goose data-stack slot,
or a C aggregate. A small leaf function can therefore stay entirely in
registers. This is not a guarantee against a native compiler spilling under
register pressure, at O0, across calls, or when the program explicitly takes
the **whole word's** address. Arrays, globals, and enclosing structs can of
course hold words in memory. Generated C establishes that storage is not
required by this feature; native assembly establishes actual residency for a
particular compiled function (§9).

The structure of this proposal follows the explicit scope, syntax, compiler
integration, and rejection-test treatment of
[const_for.md:19](const_for.md#1-scope-and-cost-model) and
[const_for.md:462](const_for.md#7-compiler-integration), and the implementation
consequences and recommendations approach in
[scope_exit_cleanup.md:1](scope_exit_cleanup.md). These are precedents for
separating proposed behavior from existing machinery, not implementations of
packed words.

## 2. Existing compiler: evidence and integration boundaries

The following are observations, not claims that this feature already exists.
All paths are relative to the repository root. The linked anchors give the
start of the relevant implementation; adjacent line intervals locate the
rest for a local reader.

| Area | Current machinery and implication |
|---|---|
| Declaration parsing | [`src/parser.h:563`](../../src/parser.h#L563), lines 563–638: `ParseStructDecl` registers `SStruct`, parses generic parameters and `ParseFieldList`; fields carry ordinary types, defaults, padding, or conditional branches. Add a sibling declaration, not a spelling alias for struct. |
| AST | [`src/ast.h:55`](../../src/ast.h#L55), `TypeKind`; [`src/ast.h:416`](../../src/ast.h#L416), `Field`; [`src/ast.h:1573`](../../src/ast.h#L1573), `SStruct`. Bit widths and offsets need their own metadata rather than byte-field offsets. |
| Checking structs | [`src/typecheck_types.h:67`](../../src/typecheck_types.h#L67), lines 67–139: `GetStructInst` substitutes field types and computes fixed/variable/resizable placement and flatness. Packed words are always fixed and flat; their fields must not enter this storage walk. |
| Constructors | [`src/parser.h:1955`](../../src/parser.h#L1955) parses `StructLit`; [`src/typecheck_nodes.h:304`](../../src/typecheck_nodes.h#L304) expands initializers and dispatches by type; [`src/typecheck_exprs.h:3041`](../../src/typecheck_exprs.h#L3041) checks named/positional fields and missing/default entries. Reuse list syntax, dispatch packed-word construction separately. |
| Conditional fields | [`src/parser.h:600`](../../src/parser.h#L600) parses both branches and marks branch-owned types/functions conditional. [`src/typecheck_expansion.h:176`](../../src/typecheck_expansion.h#L176) defines constant-condition diagnostics; lines 200–248 select and flatten fields, resolve only selected bodies, reject active duplicates, and reject type-parameter-dependent conditions. [`src/resolve.h:225`](../../src/resolve.h#L225) performs selection before checking active field types. Extend this boundary to packed declarations. |
| Integer widths | [`src/lexer.h:53`](../../src/lexer.h#L53) has unsigned keywords through u64; [`src/ast.h:95`](../../src/ast.h#L95), lines 95–145, has fixed 8/16/32/64 storage, varint, 64-bit range helpers and constant representations. There is no general u2/u21 or u128 scalar support here. [`src/codegen_types.h:199`](../../src/codegen_types.h#L199) maps existing integer storage to C. General u128 scalar support is outside v1 under the owner scope decision. |
| Enum values | [`src/parser.h:640`](../../src/parser.h#L640), lines 640–687, parses variants and optional payloads, with no explicit numeric discriminants. [`src/codegen_types.h:704`](../../src/codegen_types.h#L704), lines 704–720, assigns tags by zero-based variant index. Infer widths from those values in v1. |
| Struct C layout | [`src/codegen_types.h:606`](../../src/codegen_types.h#L606) emits struct bodies; [`src/codegen_types.h:678`](../../src/codegen_types.h#L678) emits their fields. [`src/codegen_nodes.h:372`](../../src/codegen_nodes.h#L372) creates a fixed aggregate temporary for a struct literal; [`src/codegen_construct.h:1132`](../../src/codegen_construct.h#L1132) fills it. None should become the representation of a packed word. |
| Field locations and assignment | [`src/typecheck_exprs.h:13`](../../src/typecheck_exprs.h#L13) checks lvalue paths; [`src/typecheck_nodes.h:452`](../../src/typecheck_nodes.h#L452) checks dot access; [`src/codegen_values.h:943`](../../src/codegen_values.h#L943) constructs field locations. [`src/codegen_nodes.h:842`](../../src/codegen_nodes.h#L842) pins assignment destinations, sometimes taking their address. A bit view needs a distinct write target; pretending it is an ordinary field breaks both correctness and residency. |
| Scalar ABI/equality | [`src/codegen_calls.h:124`](../../src/codegen_calls.h#L124), lines 124–151, uses `CT` for results and function-value signatures. [`src/codegen_types.h:1313`](../../src/codegen_types.h#L1313) recognizes scalar equality. Packed words must map to backing C scalars while retaining nominal checker identity. |
| Typed atomics | [`src/typecheck_builtins.h:112`](../../src/typecheck_builtins.h#L112), lines 112–185, accepts u32/u64 capabilities, enforces scalar arguments and constant memory orders, and returns observed value plus success for CAS. [`src/codegen_builtins.h:127`](../../src/codegen_builtins.h#L127), lines 127–187, requires always-lock-free native widths, validates capabilities, and emits GCC/Clang builtins. [`docs/native_memory.md:82`](../native_memory.md#L82), lines 82–125, documents alignment, ordinary-borrow exclusion, and lifetime constraints. Packed words use these contracts unchanged through explicit backing casts. |
| Existing integration-test precedent | [`test/const_if.py:1`](../../test/const_if.py#L1) tests emitted C, execution, alternating configurations, and editor behavior. Follow this pattern for a packed-word acceptance driver. |

## 3. Grammar and layout

```text
packed-decl := "packed" "word" name ":" backing "{" fields? "}"
backing     := "u8" | "u16" | "u32" | "u64"
fields      := field ("," field)* ","?
field       := name ":" field-type ("=" expression)?
             | "_" ":" unsigned-width
             | "const" "if" expression "{" fields? "}"
                 ("else" "{" fields? "}")?
field-type  := "bool" | unsigned-width | enum-type
unsigned-width := "u" decimal-width
```

Recognize `packed word` contextually at declaration position; do not reserve
`word` as a global keyword. Recognize nonstandard `uN` spellings only in the
field-type position, before ordinary type-name resolution. Canonical widths
are decimal 1 through 64 without leading zeros. `u8/u16/u32/u64` remain
ordinary unsigned types too. `u2`, `u21`, etc. are layout descriptors, never
types permitted in parameters, aliases, locals, casts, or generic arguments.
An enum field may use an ordinary alias to an eligible enum. V1 declarations
have no generic parameter lists, inheritance, field mutability modifiers,
`pad`, nested packed-word fields, array fields, or reference fields. A
packed word can still instantiate a generic function or container.

**Order only in v1.** Starting at offset zero, assign each active field the
current offset and advance by its width. Check the sum before publishing the
layout. Offsets are numeric least-significant-bit positions, independent of
host byte order. All unallocated high bits are implicit reserved bits.
Repeated `_` entries are allowed and are never duplicate field names.

Reject `@position` syntax in v1. Explicit reserved spans express holes with
one rule and make conditional replacements easy to audit; pinned positions
would add overlap detection and two competing ordering rules. Revisit only
with a concrete imported hardware/protocol format that benefits from it.

**Unsigned fields in v1; signed fields deferred.** Reject every signed field
spelling, including standard `i8`. A future `iN` can define two's-complement
insertion and sign extension to a signed carrier on read, but v1 need not
add signed narrow arithmetic and overflow semantics to layout work. Use
unsigned fields and explicit decoding when a format has signed values.

**Conditional fields.** Parse all branches, then select with the existing
constant-boolean evaluator. Lay out and type-check only active fields, even
at O0. Nested conditionals are supported; use nested blocks for else-if,
as the current field grammar does. No runtime expression, parameter, call,
or type-dependent condition is allowed. Active duplicates are errors;
identical names in mutually exclusive branches are legal.

```goose
packed word Flags : u32 {
    const if build::DEBUG { trace: bool } else { _: u1 },
    generation: u31,
}
```

Both configurations have `generation` at bit 1. Without the else reservation,
its offset would change; this is permitted, not padded automatically. Store
in layout metadata a deterministic fingerprint over nominal declaration,
backing, active names/types, enum tag mappings, offsets, widths, and reserved
spans. Tests and tools can compare it; v1 need not expose a language builtin.
FFI and persisted formats require matching configurations and fingerprints.
Bit numbering does not specify byte serialization; use explicit endian
encoding of the raw backing value for external formats.

## 4. Values, construction, and mutation

### 4.1 Field reads and enum interpretation

A bool reads as bool. A `uN` reads as the smallest unsigned carrier in
u8/u16/u32/u64 that contains N bits; e.g. `age` reads as u8 and `u33`
reads as u64. No narrow type escapes the declaration. Reads of temporary
words work without first materializing an addressed word.

Only nonempty, payload-free, fixed-mode enums are eligible. If its greatest
tag is M, width is `max(1, bit_length(M))`; a single variant occupies one bit.
In today's ordinal scheme M is variant-count minus one. Do not add explicit
discriminants as part of this feature. Empty payload syntax is still a
payload declaration and is rejected, to keep the eligibility rule stable.

The result of reading an enum field is the ordinary enum value, not a raw
integer. Extract the tag, validate it against the variants, then materialize
the existing enum representation. An invalid tag introduced through a raw
word cast aborts with a source-located error in **all builds**, rather than
creating an invalid ADT for exhaustive `match`. Validity checks may be
eliminated when proven redundant (e.g. all bit patterns name variants).
Writing an enum field requires the declared enum; insert its checked tag.
Enums with payloads cannot fit in a bit view regardless of tag width.

"Enum too wide for its inferred width" is not a separate user-controllable
case today: inference includes every variant, so it cannot normally happen.
Maintain an explicit invariant that every tag fits the inferred field width,
and diagnose violations rather than truncating (e.g. stale cached metadata).
A width larger than the remaining backing space is the ordinary layout
capacity error. Do not invent enum width annotations merely to create an
otherwise impossible negative test.

### 4.2 Whole values and conversions

`word as u64` and `raw_u64 as ObjectHeader` are representation-preserving,
zero-cost casts for matching backings. They do not validate enum fields or
clear reserved bits. `as!` has the same result for these exact pairs. Other
integer widths require an explicit intermediate backing conversion with
ordinary integer conversion semantics. Packed types are nominal: different
words do not assign or compare implicitly, even with identical layouts.
Use explicit raw casts for deliberate interchange.

Whole assignment copies every bit. Equality/inequality compare the whole
backing integer, **including reserved and unused bits**. No implicit numeric
arithmetic or ordering is introduced on words; cast to the backing for it.
`default<Word>()` uses declaration defaults as `Word { .. }` does. Without
declaration defaults this is the all-zero word; use a zero backing cast when
zero bits are required regardless of defaults. The current enum scheme makes
zero a valid tag for every eligible enum. This follows existing field-default
semantics ([docs/reference.md:1225](../reference.md#field-defaults)).

Reading or changing reserved bits via the raw integer has no special
contract: they are ordinary bits. They need not be zero, are not poison,
and do not trigger validation. Only named field access omits them. A field
update must preserve even nonzero reserved bits and invalid enum bits in
other fields. Two words with the same named fields can compare unequal.

A word is allowed wherever its backing is allowed: local/global, struct
field, array/slice element, generic argument, function argument/result,
queue payload, and whole-value reference. It has backing size and alignment
in the same storage context; enclosing Goose packed structs may use their
existing unaligned scalar access convention. Worker isolation remains the
backing scalar's isolation; no ordinary shared reference exemption is added.
For native FFI use the exact backing ABI.

### 4.3 Construction

Support `Word { field: expression, ... }` with ordinary initializer-list
syntax, including `const if` and `const for` initializer expansion. Also
allow ordinary positional construction over active **named** fields only;
never count reserved entries as arguments. Mixed named/positional lists,
unknown labels, duplicates and missing initializers follow struct errors.
Declaration defaults fill omitted fields; `..` supplies zero defaults for
remaining fields, following struct construction's explicit default form.
A bare missing field without a declaration default or `..` is an error.
No `self` readback or reference to a partially constructed word is supported.

Start from zero, evaluate each initializer exactly once in active field
declaration order, interleaving omitted declaration defaults, and assemble
the scalar with OR/shift operations. Named labels do not change evaluation
order. This matches `CheckInits` and `StructLitAt` (source references in §2). Validate every initializer before
insertion. Reserved bits and unused high bits start at zero. Defaults have
the declaration's name environment, and inactive defaults are not checked.

### 4.4 Writes and overflow

A word-field target is a *bit-update target*, not an addressable field.
`w.age = x` requires permission to replace the containing word, using whole
scalar writability rules (a `let` word cannot be mutated through its views).
The containing word must already be initialized. Preserve all bits outside
the field mask, including implicit high reserves.

Unsigned assignments accept unsigned runtime integers (up to u64) and
nonnegative integer literals. Compile-time values outside `0..2^N-1` are
errors. Runtime values are checked in all builds and abort when out of
range; proven-fitting carrier types or range facts eliminate the check.
Signed runtime expressions require an explicit unsigned conversion first.
This prevents accidental truncation in a named format. For deliberate
truncation use `w.age = x & 3` with an unsigned x. Bool requires bool, not an
integer truthiness conversion.

Support compound assignments and increment/decrement for unsigned fields.
Resolve the destination once and snapshot the selected field for the
operation, then evaluate the RHS once. Compute with checked arithmetic
against the field range (detect underflow/overflow before carrier wrapping),
then apply the same insertion rule; bitwise results must also fit. Shifts
follow ordinary carrier shift-count rules and then the field range check.
Bool and enum fields allow plain assignment only.

For plain assignment: resolve the whole-word destination and its index or
reference before evaluating the RHS; evaluate and validate the RHS; load
the latest containing word; replace the selected bits; store once. Thus an
RHS that changes a different field of the same word does not lose that
change. For compound assignment use the earlier selected-field snapshot
for the calculation but the latest whole word for merging. Existing lifetime
checks must reject RHS actions that invalidate the pinned destination.
A simple local destination must stay a scalar name, not be pinned by `&w`.

Reject `&w.age`, passing it to reference parameters (including implicit
reference adaptation), and any byte-view operation requiring its address.
Use a value temporary and explicit assignment for such APIs. Whole-word
references remain legal. Treat writes to different fields as overlapping
writes of the same word for alias/effect analysis.

`fields<Word>` reflection is deferred in v1: retain the current struct/variant
restriction. Existing field visitors often take `&value.A`
([const_for.md:421](const_for.md#6-library-use-and-receiver-semantics));
extending them silently would imply field addressability. A future value-only
layout query can expose bit offsets without that implication.

## 5. Atomics

Atomic capability storage is distinct from a local word. For a u32/u64 word,
register its raw backing with `shared_atomic_u32/u64`, load a raw scalar and
cast to the word, and cast back for store/exchange/CAS. These casts introduce
no representation work. The capability continues to be SharedAtomicU32/U64;
no new handle type, overload family, or automatic atomic field syntax is
needed. Existing orders, alignment, lifetime, and borrow exclusions apply.

An atomic update of one field requires a CAS retry loop: load the raw word,
copy to a local word, update the field, CAS expected raw against desired raw,
and on failure retry using the observed raw returned by CAS. Recompute the
candidate each time so concurrent updates of other fields survive. A normal
load/update/store can lose those updates. Evaluate any external RHS once
before the loop unless the algorithm intentionally recalculates it.

`atomic_fetch_*` on a raw backing remains integer arithmetic/bitwise work;
it is not narrow-field arithmetic (addition may carry into neighboring bits).
There are no u8/u16 capabilities in the existing API, so those words are
plain values; pack into a u32 cell explicitly if needed. u128 backings are
rejected even if a native target provides 128-bit atomic instructions; no new atomic width is introduced.
Do not add a mutex fallback or ordinary borrow of atomic bytes.

## 6. Generated C and existing scalar support

Use a distinct checker type, e.g. `TY_PACKED_WORD`, with immutable checked
layout metadata. `CT(word)` is exactly `CT(backing)`; an optional typedef to
the scalar is harmless. Do not emit C bitfields, unions, packed aggregate
wrappers, pointer casts for local field access, or runtime field tables.

For the example in §1, the essential C shapes are:

```c
/* A read: age is bits 1..2. */
uint8_t age = (uint8_t)((h >> 1) & UINT64_C(3));

/* h.age = x: x is evaluated once; h is a writable scalar local. */
uint64_t rhs = evaluate_x();
if (rhs > UINT64_C(3)) packed_field_range_error(/* source location */);
h = (h & ~(UINT64_C(3) << 1)) | ((rhs & UINT64_C(3)) << 1);

/* Constructor: locals below already evaluated/validated in declaration order.
   kind_tag has been extracted from a valid ObjectKind value. */
uint64_t h = ((uint64_t)marked << 0)
           | ((uint64_t)age << 1)
           | ((uint64_t)kind_tag << 3)
           | ((uint64_t)size_class << 4)
           | ((uint64_t)forwarded << 10)
           | ((uint64_t)type_id << 32);

/* Word parameter and result are scalar, as are copies and equality. */
uint64_t set_marked(uint64_t h) { return h | UINT64_C(1); }
```

Names above are illustrative lowering, not existing runtime helper names.
For a stored word, stabilize the actual whole-word location once and use the
ordinary backing load/store path, including unaligned-safe access in a packed
struct. Never invent an address for the selected bits. Bool extraction uses
one bit and normalizes to the existing bool representation.

For backing width B, field width W and offset O, define the mask at compile
time as all ones when W == B, otherwise `(U(1) << W) - U(1)`. Never shift by
B. Perform shifts/bitwise operations in an unsigned calculation type at least
as wide as the backing and at least 32 bits (avoid signed promotions for
u8/u16), then cast the completed result back to the backing. Width and offset
arithmetic in the compiler must be checked before mask formation.

### 6.1 Scope of scalar work

Reuse the existing u8/u16/u32/u64 scalar types, constants, arithmetic and C
mapping. Do not add a u128 keyword/type, widen constant storage, or introduce
128-bit code generation, formatting or serialization. Field descriptors and
carriers cap at 64 bits; full-width masks use all ones without shifting by 64.
The register-residency objective remains u64 on Linux x86-64, with no new
execution-verified platform claim.

A declaration naming `u128` receives one clean diagnostic:
`128-bit packed word backings are not yet supported`. It cannot produce an
aggregate representation or generated C. Wider formats compose ordinary
structs containing multiple supported words; a future u128 design needs a
concrete two-word use case and separate approval.

Native-memory width allowlists, u32/u64 atomic capabilities, and CLI
build-definition integer ranges are unchanged.

## 7. Diagnostics

Report the field/type span, declaration name, relevant widths/offsets, and a
secondary location for the previous declaration when appropriate. Examples
below are proposed exact primary messages (names substituted as shown).

| Trigger/example | Primary diagnostic |
|---|---|
| `packed word Small : u8 { a: u6, b: u3 }` | `packed word Small uses 9 bits, exceeding u8 backing width 8; field b occupies bits 6..8` |
| `packed word W : u64 { a: u2, a: bool }` | `duplicate field name a in packed word W` (note first a; active branches only) |
| `a: u0` or `a: u65` | `packed word field width must be between 1 and 64; found u0` (substitute u65) |
| `packed word W : u24 {}` | `packed word backing must be u8, u16, u32, or u64; found u24` |
| `a: i3` | `signed packed word fields are unsupported in v1; use an unsigned field and explicit decoding` |
| `a: u2 @ 4` | `explicit packed word field positions are unsupported in v1; use reserved fields` |
| Payload enum E / empty enum E as field e | `packed word field e requires a nonempty payload-free enum; found E` |
| Invalid metadata: enum E tag 4 with cached width 2 | `enum E variant tag 4 does not fit inferred width 2 for packed word field e` (compiler metadata regression test, not reachable source syntax today) |
| Three-variant E in `packed word W : u8 { _: u7, e: E }` | `packed word W uses 9 bits, exceeding u8 backing width 8; field e occupies bits 7..8` (note E needs 2 bits for largest tag 2) |
| `w._` or `W { _: 1, .. }` | `reserved packed word bits have no field name and cannot be accessed or initialized` |
| `w.age = 4`, age: u2 | `value 4 does not fit packed word field W.age (u2, range 0..3)` |
| Runtime out-of-range age | `packed word field W.age value is outside range 0..3` (abort, source location) |
| Raw enum tag 3 for three-variant E on field read | `invalid enum tag 3 in packed word field W.e (E)` (abort, source location) |
| `&w.age` / reference argument | `packed word field W.age is a bit view, not addressable storage; reference the whole word or copy the field` |
| `packed word W : u128 {}` on any backend | `128-bit packed word backings are not yet supported` |

Reuse existing unknown-field, constructor missing/duplicate initializer,
const-expression and immutable-destination diagnostics with packed-word
names. Unsupported field types must say `packed word field requires bool,
unsigned bit width, or payload-free enum`. Parser recovery must preserve
later declarations rather than treating the rest of a bad layout as fields.

## 8. Implementation phases and risks

Estimates are changed handwritten lines (additions plus substantive edits),
not commitments; generated parser artifacts are excluded. These were the
approved planning estimates. Phase checkpoints and measured validation results
are recorded in the [implementation report](../evidence/packed-word-validation.md).

| Phase | Files and deliverables | Rough size |
|---|---|---|
| 1. Parser, AST, tooling | `src/parser.h`, `src/ast.h`, `src/dump.h`, `src/resolve.h`, LSP and editor grammar files: nominal declaration, descriptors, conditionals, source preservation and explicit u128 rejection. | 350–500 lines |
| 2. Checker and layouts | `src/typecheck*.h`, `src/ast.h`: selected layouts, width/carrier/range rules, enums, exact backing casts, construction, mutability and bit-view reference rejection. Existing scalar storage remains unchanged. | 500–750 lines |
| 3. C generation | `src/codegen*.h`: scalar mapping, masks, checked extraction/updates, once-only evaluation, scalar ABI/equality and stored-word handling. No 128-bit runtime additions. | 400–600 lines |
| 4. Tests | `test/packed_word*.py`, syntax/editor fixtures and `test/run_tests.py`: all four backings, preservation, conditionals, enums, placement, atomic CAS, native/JIT execution and residency evidence. u128 coverage is rejection diagnostics only. | 550–850 lines |
| 5. Documentation | Reference, specification, implementation notes, native-memory/configuration docs, this design, and `samples/packed_word`. | 200–300 lines |

Revised total: approximately **2,000–3,000 handwritten lines**. Report any
growth beyond that range with its reason. The largest remaining risk is
addressability and aggregate assumptions in existing checker/codegen paths;
there is no general u128 scalar prerequisite in this scope.

Key risks and acceptance gates:

* **Addressability assumptions.** `FieldLocAt`, `GenLoc`, construction, unary
  address-of, implicit reference adaptation, and assignment pinning assume
  ordinary fields denote storage. Introduce an explicit checked bit target
  (whole-word root, stable destination, field descriptor), not a fake `Loc`
  with a mask expression as its lvalue. Audit inc/dec and compound assignment
  separately. A scalar local update must not acquire an address accidentally.
* **Nominal versus physical type.** Equality, mangling, overload selection,
  cloning, generic caches, flatness, byte images, ABI headers, and rendering
  must retain word identity while using backing storage. A catch-all type
  switch that falls through to struct handling is a correctness defect.
* **Constant width assumptions.** Keep the existing scalar constant storage.
  Full-width u64 masks must avoid shifting by 64; reject widths above 64 before
  mask formation. Do not introduce signed promotions or truncate u64 literals.
* **Enums and raw casts.** A free raw cast permits invalid enum encodings;
  extraction must validate before creating an ordinary enum. This is a field
  read cost, not a whole-word conversion cost. Do not claim enum extraction
  itself always stays in one register: existing enum values are aggregates.
* **Conditional state.** Source field trees and selected layout metadata must
  remain separate for diagnostics/editor recovery. Never reuse a layout
  across different build definitions; parse errors in excluded branches
  still fail. Width/duplicate errors there must not fail selected builds.
* **Stored words and concurrency.** Nested struct locations may be unaligned;
  use scalar-safe loads/stores rather than imposing atomic alignment on all
  words. Atomic storage remains accessed only through capabilities. Field
  writes are whole-word effects, including for optimization and aliasing.

## 9. Test and evidence plan

Use `goose++` on PATH for the fork. Tests create all generated C, executables,
and assembly in temporary directories and remove them on success and failure.
Run the repository's ordinary fixtures and relevant conditional/native-memory
regressions after the focused suite. Acceptance drivers remove their temporary
C, binaries and assembly.

1. **Layout and diagnostics.** Backings 8/16/32/64; zero named fields;
   repeated reserves; implicit trailing reserves; exact fills; one-bit
   overflow; every legal narrow width; invalid 0/65 widths/backings; signed,
   pointer, array, nested-word and payload-enum field rejection. Verify the
   §1 offsets using independently computed integer masks. Assert source
   locations and diagnostics, including duplicate names after flattening.
2. **Preservation and values.** For every field, seed the whole word with
   zero, all ones, and alternating patterns; write zero/max/random values;
   assert `(after & ~mask) == (before & ~mask)` and extraction equals input.
   Test full-backing-width fields, bool normalization, reserved-bit raw
   roundtrips, equality differing only in reserves, defaults, named and
   positional construction, declaration-order evaluation, checked overflow,
   unsigned increment/decrement and compound overflow before carrier wrap.
   Test a RHS that updates a neighbor and receiver/index side effects.
3. **Placement and mutability.** Words in ordinary structs, fixed/growing
   arrays, generic functions, function values, arguments/results, worker
   messages and whole-word references; unaligned containing struct offsets;
   let/const rejection; field address rejection through generic reference
   adaptation. Confirm whole-word copies stay independent. FFI roundtrip
   tests use exact supported backing signatures.
4. **Conditional layouts.** Alternate `-D DEBUG=true/false` in fresh
   processes and editor sessions. Verify same-width reserved alternatives,
   deliberately shifting offsets without else, nested conditions, active
   duplicates, excluded semantic errors, included errors, and excluded parse
   errors. Check constructor expansions and omitted inactive defaults. At O0
   inspect emitted C for absence of inactive fields/default expressions.
   Compare layout fingerprints across configurations.
5. **Enums.** Counts 1, 2, 3, 4, 5, 256, 257 give widths 1, 1, 2, 2, 3, 8,
   9. Check each variant tag and readback, payload/empty enum rejection,
   enum-growth capacity failures, invalid raw tags trapping on extraction
   (including a single-variant enum's tag 1), and no trap for copying/casting
   such a raw word or updating unrelated fields. Inject a mismatched width
   in a checker unit fixture for the otherwise unreachable width invariant.
6. **Deferred u128 rejection only.** Empty and populated u128-backed
   declarations must each produce exactly one explicit unsupported-backing
   diagnostic under parse/check/native generation, at O0 and O2. Verify no C
   or aggregate fallback is produced. Fields u65/u127/u128 and larger fail
   the 64-bit descriptor limit. General u128 declarations and literals above
   u64.max remain rejected by the existing scalar rules. No positive scalar,
   seam-crossing, formatting or serialization tests belong in v1.
7. **Atomics.** u32/u64 raw-cast load/store/exchange/CAS roundtrips and
   contended disjoint-field CAS updates with final counter checks. Verify
   stale/misaligned/out-of-range capability errors and ordinary borrow
   exclusion still work; invalid order tests remain rejected. Ensure rejected u128 backings
   cannot enter atomic APIs and plain `w.field = ...` emits no atomic call.
8. **Register-residency evidence.** Add externally observable noinline leaf
   kernels taking and returning a u64 word: extract age, replace a known-fit
   field, construct from known-fit inputs, and equality. Compare to handwritten
   u64 kernels. Inspect emitted C for scalar signatures and locals, masks
   and shifts, with no aggregate wrapper, address-of-word, `memcpy`, allocation,
   or Goose stack access. Compile that C with supported GCC and Clang at O2;
   inspect the leaf symbols' disassembly for register arguments/results and
   **no stack loads/stores, stack allocation, or helper calls** on the normal
   known-fit paths. Do not depend on one exact instruction sequence. Include
   a non-inlined caller/callee boundary so inlining cannot hide a bad ABI.
   Record compiler versions, target, flags and extracted symbols in test
   evidence. O0 is a semantics/C-shape check, not a no-spill requirement;
   pressure-heavy and address-taking cases are explicit counterexamples to
   a universal physical-register guarantee. Before implementation these
   tests are a plan, not claimed measured evidence.

## 10. Decisions for implementation

Proceed with order-only fields, unsigned narrow descriptors, explicit free
backing casts, checked writes, and nonaddressable field views. Preserve every
raw bit outside the written field and compare all bits for equality. Infer
payload-free enum widths from current ordinal tags and validate raw enum
encodings at extraction. Reuse existing u32/u64 atomic capabilities through
raw casts and CAS loops. Ship only u8/u16/u32/u64 backings and cap descriptors
and carriers at 64 bits.
Per the owner decision of 2026-10-31 23:51 ET, defer u128 and all general
128-bit scalar work until a concrete two-word need drives a later round.
Reject a u128 backing with the explicit diagnostic in §7, never an aggregate
fallback. Defer pinned positions, signed fields, generic packed declarations, and field reflection. None of
these deferrals changes the owner's single-integer representation or
conditional-layout decisions.
