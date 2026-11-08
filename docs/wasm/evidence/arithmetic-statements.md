# Fixed aggregate arithmetic statements

The Wasm backend now lowers `+=`, `-=`, `*=`, `/=` and `%=` for the numeric
structs and fixed arrays admitted by the frontend. Scalar multiplication and
division keep the frontend's common leaf-type rule. Limited arrays, slices and
differently typed array operands retain their existing frontend rejection.
Discarded fixed unary minus now uses the existing checked temporary path, as
discarded fixed binary arithmetic already does.

`AssignFixed` receives the captured destination. It does not reconstruct the
original lvalue, so receivers and indices run once. Before an effectful right
operand, the existing bounded syntax scan selects one private copy of the old
left value. Scalars are captured once before stores. Aggregate operand owners
remain live through the existing numeric leaf helper. Ordinary pure right
operands use the captured destination without an old-value copy.

Compound updates write numeric fields and elements in order. A failure in a
later leaf leaves earlier stores visible, matching the native backend. This
path therefore does not construct and copy a whole protected result. Padding
stays untouched. The existing temporary scopes restore old-value copies on
normal completion and early control exits.

## Correctness evidence

Twenty-two compound-assignment cases and three discarded-negation cases pass
natively and fail to compile on the parent Wasm backend. Twenty-nine positive
families now pass at O0/O2 in native code, Node and Wasmtime. They cover all five
operators, narrow signed limits, unsigned arithmetic, mixed-width fields,
nested fixed rows, float scalar aliases, effectful and rebound reference
receivers, indexed packed rows, large repeated snapshots, empty operand effects,
early returns/continues and one shared reference function called with different
data memories.

Fifty-eight Node observer/control checks pass:

- Thirty compare complete mixed-F32/F64 images, padding and sentinels in Memory
  0 and separate data memory. Signed-zero and infinity bits are exact. NaN
  results must be quiet; payload/sign variation is permitted only for the two
  result leaves. Valid wrong operations, offsets, padding stores and memory
  selections fail named image assertions.
- Four inspect complete old-value snapshots while an RHS mutation is active
  and after it returns. A valid read from the changed original source fails
  the result-image assertion.
- Eight inspect live loop tops for compound early `continue` and discarded
  negation. Valid missing-restore controls fail before final cleanup can hide
  them.
- Four check the global row owner's exact final top and full data-memory image.
  Valid wrong-top controls leave computed values intact and fail the owner
  state assertion.
- Twelve check division/modulo by zero and signed division overflow after the
  first leaf was stored. Generated native C is preserved, with a separate
  diagnostic copy observing both permanent array elements immediately before
  the expected abort. Native and Wasm agree on the partial result. Valid Wasm
  missing-store controls fail the complete permanent-image assertion.

The complete Wasm suite passes 4,047 checks. The native baseline passes all 18
groups, including 2,544 frontend, 1,248 generated-C and 1,423 TinyCC checks.
All 52 exact shared-backend comparisons pass. All 970 parent Wasm fixture
modules are byte-identical using completed suite outputs, without guest reruns
for the identity comparison. Execution evidence is from Linux.

## Preserved failures and limits

The first compound prototype checked `T_PLUSEQ`-style tokens, although Statement
already passed normalized arithmetic operators. A read-only search found this
error; its actual native-valid array rejection was recorded before correction.
The corrected guard uses the operators it receives. The first build and failed
check remain unchanged.

Three preparation fixtures were invalid: a joined `&=` token in a reference
declaration, signed array literals for unsigned compound arithmetic, and direct
assignment to a returned reference expression. Separate corrected fixtures
preserve the intended reference, unsigned and receiver coverage. The initial
completed-owner check also incorrectly expected a global data array's top to
return to 1. The continuation verifies and reuses passed artifacts and commands,
then checks the global owner's actual persistent state.

The bounded effects scan has the same 64-node limit as binary construction.
A selected old-value copy uses bytes proportional to the fixed aggregate image;
that copy is needed to preserve the value before RHS mutation. Leaf work is
proportional to the aggregate size. There is no new persistent compiler state or
runtime allocation service. Performance and physical-memory measurement are
excluded by the correctness-only owner directive.

The complete backend remains unfinished. Other gaps include arithmetic into
variable/growing receivers, zero-sized aggregate calls, general slices and
remaining compound lifetimes and host adapters. These checks do not claim those
forms work.

Raw evidence is in `/tmp/goose-wasm-compound-math-20261108`. The
[archive manifest](arithmetic-statements/archive-manifest.json) records frozen
source and inputs, compiler identities, commands, failures and final checks.
Binaries and complete generated artifacts stay in the raw directory.
