# Array iteration through fixed aggregate fields

Valid field-array loops previously stopped with `field-path iteration needs
the pending path lowering`. Native behavior and the exact old Wasm failure
were recorded before changing the compiler. They now compile directly to Wasm
and agree with native output in Node and Wasmtime at O0/O2.

The new captured place walk records field selectors and evaluates each index
once. It resolves mutable root references and reference slots again at each
loop test. An effectful index first captures its parent and count, then runs
the index expression. Later fields and reference slots still reload. This
matches the existing native location rules and retains the old indexed-array
walk for paths without fields.

Field layout, exact accessor type, checked field offsets, null checks, current
outer bounds and element addressing use existing services. A field's actual
memory travels with its place, including unaligned fields inside data-memory
rows. Copied nominal binders use the existing fresh Memory 0 owner and copy
service. By-reference and scalar/reference binders use their previous binding
rules. No source-language or serialized-layout change is introduced.

Ten positive families cover fixed and limited fields, zero visits, mutable
roots, rebound array-reference fields, data-array row fields, an index that
changes its parent reference, reference elements, growable outer reference
arrays, function-returned references and enum payload fields. Completed-owner
checks run for each permanent field fixture. A separate safety case rebinds an
outer array to an empty array: the next index test fails with index zero and
length zero, after exactly one printed visit, in native code and both engines.
Direct iteration over a nullable array field remains a frontend rejection.

The integrated `--correctness-only` suite passes 1,409 check groups, including
the complete forty-case Memory 0/data image matrix, live recursive-frame
observer and validated shared-frame control. The compiler is frozen as SHA256
`110f0865866bfc0668a581e47f4569b97feb31020eb1242f83587373b25379e9`.
All 80 C++ input hashes match. The final run checks its test and adapter input
hashes before and after execution. This mode skips cost-only scaling reports;
it does not use a measurement lease or perform timing work.

The native baseline passes 1,800 parse/roundtrip/typecheck checks, 876 generated
C runs, 1,048 TinyCC runs and all other baseline groups. That baseline precedes
the two final permanent call/variant fixtures; their native and two-engine
O0/O2 behavior is checked separately and in the final Wasm suite. All 52 exact
comparisons pass, and all 272 unchanged-source parent modules are byte-identical.

The initial integrated run stopped at a stale `field-for` negative assertion.
That test and the corresponding aggregate-field assertion now execute the
admitted modules; unrelated rejection checks remain. A first zero-trip fixture
used a zero-length struct field, which native Goose rejects. Its source and
error remain preserved; the valid replacement uses an empty limited field.
Neither setup failure required a compiler change.

Raw records are under `/tmp/goose-wasm-field-iteration-20261107`; selected
identities, statuses and failures are in
[field-iteration](field-iteration/archive-manifest.json). The earlier copied-data
review and its real-recursion correction are recorded separately in
[data iteration evidence](data-aggregate-iteration.md). That review does not
claim coverage of this later field-walk code.

This is correctness-only compilation work. There are no performance results
or measurement acceptance gates. Whole aggregate replacement, general
by-value calls/results, owning nonfixed aggregate fields, root/relative layouts
and other listed Stage D/E gaps remain unfinished.
