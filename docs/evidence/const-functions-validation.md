# Compile-time scalar functions v1: implementation evidence

Branch: `feat/compile-time-functions-v1`, based on fork master
`f48d26c2cd77b144cbcb782d8525b129a1a2bf96`. Implementation checkpoints:
`ebaf4d32`, `a699ba7d`, and `db49e18f`; the delivery commit adds documentation
and evidence only. No push, PR, upstream publication, or Claude review.

Authority: `docs/design/compile_time_functions_v1_trim.md` at
`design/compile-time-functions` (`c9328ff9`), read in full before the full
`compile_time_functions.md` background document. The trim takes precedence.

## Delivered behavior

Top-level `const fn` declarations have closed bool/u64 signatures and a single
return expression. The scalar shape checker validates unused declarations and
both expression-if arms, annotating existing expression type fields. It never
specializes a function or evaluates dummy arguments. Both scalar evaluators
reuse their existing arithmetic, comparison, overflow, and boolean rules.
Arguments evaluate once in the caller, then bind in a fresh scalar environment.
Global argument evaluation retains the initializer visiting set and clears the
callee's parameter environment. Active cycles, depth, parameter count and
shared request work are bounded.

Typed scalar global const requests normalize to literals. Original initializers
remain in `sourceinits`, are used by dumps and clones, and are reevaluated by
constant-global lookup. Every compilation/LSP snapshot owns fresh source and
configuration. There is no retained value cache. Marked functions cannot become
runtime calls or function values; standalone and exemplar checks skip them.
The codegen boundary asserts that no marked specialization exists.

Integer pattern calls needed five parser adapter lines and traversal through
their arguments. This is the trim's promised existing integer-pattern context,
not a new context registry. `const for` uses the existing `[expressions]` source;
no new source kind was introduced. The tree-sitter grammar uses existing
function and call nodes.

## Footprint

Count physical added/changed final compiler lines against `f48d26c2`, including
comments and blank lines. Replacements count once, as their added final lines;
removed versions are not counted a second time. All 213 lines of the one new
helper header are included. The total is **341**, within **295–455**.

| Trim section 6 piece | Actual lines |
|---|---:|
| Declaration marker and round-trip spelling, including integer pattern syntax | 16 |
| Signature/body whitelist and bool/u64 kind validation | 97 |
| Scalar binding, evaluator call/if dispatch and typed fitting/results | 96 |
| Scalar global normalization and source retention | 41 |
| Constant name traversal and scope validation | 26 |
| Call guard, limits and diagnostic notes | 37 |
| Runtime escape rejection and standalone/exemplar skips | 7 |
| Declarations, includes and invariants | 21 |
| **Total** | **341** |

The file-level accounting is 338 `src/` added/changed lines, two tree-sitter
grammar lines, and one CMake compiler-header registration line. Seven other
CMake lines register tests and count with tests. The new header's allocation is
97 whitelist lines, 52 binding/fitting lines, 33 normalization lines, 16 name
resolution lines, 10 guard/diagnostic lines, and five header/invariant lines.
Other adapters are allocated by their responsibility, without double counting.
Per-piece ranges in the design were estimates; the hard total gate is met.

Tests and test registration add 342 lines; user documentation and the sample
add 69. Total implementation/test/user-documentation footprint: 752 lines.
Evidence logs and this report are counted separately. No AST node kind,
interpreter instruction engine, aggregate value type, dependency graph, cache,
LSP subsystem, or emitter was added.

## Baseline and branch suites

Linux x86-64; GCC 14.2.0, installed Clang 23.1.3, embedded TinyCC. These runs
make no execution claim for other platforms. The compiler host build used GCC
Release flags on master; the development branch compiler used `-O0 -DNDEBUG`.
Generated Goose/native test optimization levels and runner options were the
same in both runs. No performance comparison is claimed.

The unmodified-master runner and corpus were recorded before compiler edits.
A stale preexisting `build/goose` initially lacked the already-landed record
reader. A fresh build corrected those failures. Moving the fresh executable
outside the repository lost stdlib discovery; copying it into a task build
directory restored discovery, and copying its bundled `tcclib` fixed the
packaged-JIT test. The final baseline below uses that complete fresh package.
The existing benchmark lock and running measurement were left intact.

```sh
MISE_CLANG_VERSION=23.1.3 python3 test/run_tests.py \
  --exe build-ctf-task/goose --profile baseline --cc native --require-clang -j 8
MISE_CLANG_VERSION=23.1.3 python3 test/run_tests.py \
  --exe build-ctf-task/goose-feature --profile baseline --cc native --require-clang -j 8
MISE_CLANG_VERSION=23.1.3 python3 test/const_functions.py build-ctf-task/goose-feature
MISE_CLANG_VERSION=23.1.3 ctest --test-dir /tmp/goose-ctf-build \
  -R '^const_functions' --output-on-failure
```

Tree-sitter CLI 0.25.8 was installed in temporary copies of `tree-sitter/`;
`generate` and the complete `test` corpus ran there, with the new expected tree
reviewed and a final unmodified `test` run. Generated parser files and npm
artifacts were removed with those copies.

| Gate | Master | Branch |
|---|---:|---:|
| Full baseline-profile runner | 5,727 pass, 2 fail | 5,733 pass, 2 fail |
| Complete tree-sitter corpus | 27 pass, 0 fail | 28 pass, 0 fail |
| Focused acceptance driver | unavailable | 413 checks pass |
| Registered const-function CTests | unavailable | 2 pass, 0 fail |

Both suite failures are exactly **benchmark declarations** and **benchmark
compatibility**, each reporting the occupied shared-native benchmark lock.
There are no introduced failures. The six extra runner successes cover the
new fixture/rejection and focused acceptance registration.

[Baseline runner](const-functions-baseline.txt),
[branch runner](const-functions-suite.txt),
[baseline corpus](const-functions-corpus-baseline.txt),
[branch corpus](const-functions-corpus.txt),
[focused acceptance](const-functions-focused.txt),
[CTest](const-functions-ctest.txt),
[source-retention harness](const-functions-source.txt).

## Acceptance gate, item by item

1. **PASS.** All four NEED combinations and all three width-table
   configurations run under Goose O0/O2, with check, C generation, JIT run,
   native build and native execution. NEED also selects fields/constructors
   across alternating CLI inputs. Generated C has no marked width/NEED helper
   prototypes, bodies or calls; the specialization invariant independently
   prevents marked runtime emission.
2. **PASS.** All 65,536 16-bit inputs, zero, u64.max and neighbors of every
   power of two through bit 63 are checked at O0 and O2: 65,680 distinct values
   against Python's independent `max(1, n.bit_length())` oracle. Compile-time
   branches deliberately call an unknown function on a mismatch. Native/JIT
   table reads yield `[1,5,8]`, `[1,5,10]`, `[1,5,11]`, with record array extents
   2, 2, 3. Zero and high-bit fitting are included.
3. **PASS.** Check/parse/roundtrip/O0/O2 cover sizes, capacities, fill counts,
   integer call patterns, integer const-for list entries, body/field/constructor
   conditions, and ordinary named results. Excluded semantic errors stay
   excluded; excluded parse errors fail. Existing suite contexts retain their
   behavior and diagnostics.
4. **PASS.** The driver rejects scalar-kind mismatches, negative u64 arguments
   (including CLI input), overflow literals, arity errors, ordinary calls,
   free globals/build names, layout queries, loops, locals, strings, arrays,
   signature aliases/qualifiers/defaults/generics, overloads, export syntax,
   casts, and direct/indirect runtime escapes including wrappers and defaults.
   Existing parse-only/typecheck-error phase contracts pass.
5. **PASS.** Both if arms are structurally checked; bad unselected kinds and
   free calls fail. A valid unselected division by zero and self-call do not
   execute; taking the fault/cycle fails. Both true-OR and false-AND still
   evaluate their faulting operands. Bool-valued expression-if is exercised.
6. **PASS.** Direct/mutual active cycles, global argument cycles, forward
   globals/functions, namespace-local callee resolution, local/nested-function
   shadowing, nested caller arguments, and evaluate-once argument binding are
   exercised. Exact 16/17-parameter, 32/33-active-call, and
   9,999/10,000/10,001-visit boundaries are checked. Work across repeated global
   arguments is shared, not reset. JSON diagnostics verify operation file/line
   and related requesting locations, including exhaustion after a call returns.
7. **PASS.** Check/build/native runs alternate CLI values and edited helper
   bodies. Three LSP configurations each edit the helper to produce an error
   and restore it, checking fresh diagnostics. The C++ source-retention harness
   verifies six fresh configurations/helper edits: checked typed literals,
   untouched original call trees, dump retention and source-preserving clones.
   No specialized hover/navigation work was needed.

## Corrections during validation and delivery

The first branch suite caught an extra early checker duplicating deferred-work
reports, an ordinary-call constant-source diagnostic changing unnecessarily,
and body validation running in the parse-only phase. Validation now runs in the
ordinary checker before layouts, or in the existing early field checker when
needed; integer call dispatch leaves ordinary calls to the old rejection path.
Focused tests caught a test helper named `f32` colliding with the primitive
keyword; the depth boundary now uses `depth32` and asserts the actual limit
message. Request notes remain available after an active helper returns, and
adaptable `~0` arguments use the existing u64 fitting rules. Final evidence
includes these corrections.

**Deviations from the trim: none.** Additional tests directly inspect AST source
retention, and the existing grammar needed a small pattern-call adapter to
fulfill the specified context. Neither adds language scope. All changes are
checkpointed. Task-owned compiler/package build directories and temporary
native outputs are cleaned after validation; preexisting build directories are
not removed. Nothing was pushed and no PR was created.
