# Fresh fixed enums and standalone variants

This Stage D increment passed functional validation and read-only review. The
complete backend task and performance acceptance remain open.

## Behavior

Fixed enum and standalone variant owners use planned Memory 0 places. Shared
bounded queries compute the tag width, maximum payload and packed field offsets.
A standalone variant validates its selected payload independently of other
variants in its parent. Ordinary reference graphs are checked before a successful
admission is cached. Nonfixed enums, relative links and compound elements stay
guarded.

Fresh literals and checked defaults construct fields in declaration order.
Exact fresh copies preserve the stored image. Empty standalone variants reserve
one identity byte; an empty enum payload adds no byte after its tag. Nested
writes prove their range within the fresh owner's logical image.

Statement matches capture the source place and tag once. The selected payload
is copied to a separate planned owner before the arm body runs. The arm uses the
existing cleanup scopes, including return, break, continue and defer. A wildcard
does not admit an invalid tag. Failure code 14 reports `invalid fixed enum tag`
through the existing host contract. This adds no host import.

General by-value arguments/results, aggregate assignments/operators/printing,
value-producing matches, adapted variant images and aggregate elements retain
diagnostics. This does not add an aggregate temporary or closure ABI.

## Checked callback repair

The first Release compiler passed 17 of 18 enum fixture/optimization pairs but
rejected the combined inline-reference/callback fixture at O2. Independent
source analysis found that address scanning and binding walked `Children`,
which exposes unchecked callback templates. Runtime emission uses the checked
`fvbody`. Inlined declarations and copied payload binders in that body were
therefore absent from the binding plan.

The error was reproduced with native-valid scalar local/address, struct inline
callback and enum callback-match fixtures before repair. Both the committed
struct compiler and the first enum compiler rejected the relevant scalar/struct
cases with `out-of-line captured locals are not implemented`. Some O0/default
forms passed and remain recorded as controls. The diagnostic script's broad
all-forms-must-fail expectation returned 1; its actual per-case statuses were
retained.

Both scans now use the existing checked `RunChildren` walk. The repaired Release
compiler and all fourteen native-valid fixture sources pass at O0/O2 under Node
and Wasmtime, including the original failing fixture. The repair adds linear
compile-time traversal of checked callback bodies; it adds no runtime allocator.

## Evidence and setup corrections

The preserved repaired compiler is
`/tmp/goose-wasm-fixed-enum-20261107/build02/goose-tested`, SHA-256
`250902481fe28fadfd7102f7ac64475814c864dbc91ff2060ce5b9ed360eb73c`.
Its C++ source hashes were checked before preservation. Tests and controls are
being extended without changing that compiler source.

The original empty fixture used reserved identifier `pad`; native emission
rejected it before any Wasm behavior claim. Only that name was corrected to
`padded`, then the corrected fixture passed native O0/O2. The eight already
passed fixture sources were not rerun in that continuation.

The first remaining-check unit passed all completed owner-state checks and both
control-source pairs. Its aggregate status was 1 because a temporary match was
invalid in the native frontend and the variable enum reached the selected
nonfixed-variant guard rather than the expected parent-enum guard. Neither was
a production failure. The invalid source is excluded from native-valid target
admission counts. All raw attempts remain separate.

## Footprint and pending measurements

The dynamic-source-to-Memory-0 copy helper has one shared case per source memory.
Its function body is 79 bytes for 3 memories and 1,133 bytes for 65 memories. The
existing general two-dynamic-identity helper is 286 and 78,158 bytes respectively.
Both-known copies remain direct. This is static emitted-code evidence, not a
runtime benchmark. Valid/invalid memory identity, overlap and out-of-bounds
no-write checks passed in Node and Wasmtime for 3/65-memory modules.

Match comparisons grow with the listed variants. Payload copies take time
proportional to active payload size; exact fresh enum copies use their full
fixed image. Frames sum all bound slots, including mutually exclusive binders,
and memory growth retains pages. No slot reuse or physical RSS claim is made.

Compiler CPU/RSS, allocations and guest throughput for this increment remain
unmeasured. A coordinated handoff must compare accepted struct compiler `7fdb4c22`
with repaired enum compiler `25090248`, including scalar controls, checked
callback scans, deep field paths, 32/256-element literals, large fills, empty and
large payload matches, thin/packed reference copies and 3/65-memory helper
cases. It must keep compilation, initialization and execution phases separate,
record exact source/tool/engine identities, and report retained memory and
native-code/module sizes. No closed scalar timing grant is reused.

The complete Wasm suite passed 744 checks with wasm-tools 1.262.0, Node
24.22.2 and Wasmtime Python 49.0.0. This includes diagnostic/static controls
and executions, not 744 independent programs. The enum limited-field constructor
uses 28 locals at both 32 and 256 elements and O0/O2. Modules are 10,343 and
73,972 bytes; initializer code still grows with the number of expressions.
The earlier struct control remains part of the full suite.

The complete native baseline passed on the same preserved compiler with four
workers and the explicit TinyCC library path. Existing device/platform and
unsupported JIT skips remain in the saved log. This is Linux-native evidence;
it does not establish native behavior on other operating systems or CPUs.

All 52 saved C/report/diagnostic/scalar-Wasm comparisons passed. Of 136
prior-module pairs, 130 are byte-identical. The six changed modules are the
O0/O2 struct cleanup, reference and packed-call fixtures. Saved dumps show
only the new copy helper, destination conversions and the unused generic-copy
signature removal. Other normalized instructions and module data match.
Sizes fall by 105 or 106 bytes in four pairs and 1,275 bytes in two pairs.
These are size results; runtime speed remains unmeasured.

The [independent Astra review](fixed-enums/astra-review.md) inspected all 53
source/test/documentation scope files and verified the staged/snapshot hashes
before and after review. It found no confirmed production defect. It also
independently checked the six changed module pairs and the saved artifact
identities. It ran no builds or tests. Its report distinguishes files read from
hash-only evidence, lists context limits, and leaves compiler/runtime/physical
memory costs unmeasured. No source or test change followed this review.

The review suggests a future unequal-nonempty-payload neighbor control and wider
callback/default data-owner cases if that path grows. No failing current case
was established. The measurement handoff is in `docs/wasm/measurements.md`; the
brief mistakenly named a nonexistent `report/measurements.md`. The reviewer
read the actual available handoff. Generated Python bytecode changed after the
test manifest; the C++ and test source identities match. These limits are
recorded without altering the original report.
