# Fixed-size array arguments

Fixed and statically limited arrays now pass by value to direct functions,
inline bodies and function-value bodies. Existing fixed-layout admission
remains authoritative. Zero-image parameters, nonfixed array values and array
results remain guarded in this step. Scalar and reference ABI values are
unchanged.

One shared parameter rule selects fixed nominal values and inline array images.
The storage pass records each real direct parameter, callback parameter and
inline argument declaration. Direct calls capture complete Memory 0 snapshots
at each argument's evaluation point; the callee copies each snapshot into its
own planned frame slot. Inline and callback bodies construct their own real
parameter owners. No fake frontend node or runtime descriptor is added.

Parameters keep value isolation, including length headers and inactive limited
capacity. They can change without changing the source or another parameter.
Reference elements remain shallow references. Ordered cleanup handles early
argument returns, function defers and nested calls. Mixed scalar/reference
arguments and scalar/nominal results keep their evaluation and capture order.
Dynamic data-stack bases remain separate from the parameter addresses and the
hidden nominal result destination.

The native-first set covers direct, inline and callback calls; fixed/limited
arrays; scalar, float, bool, reference and nominal elements; source literals,
defaults, fills, strings, globals, fields, data fields and dynamic source memory
identities; independent parameters; recursion; later-argument returns in all
three call forms; active data memories with reference elements; large frames;
16/32-bit length prefixes; and mixed nominal results with dynamic data-stack
bases. The final set has twenty-nine families, or fifty-eight O0/O2 cases. Both
Wasm engines pass the targeted functional cases.

A complete Memory 0 observer seeds inactive capacity bytes in a nine-byte
limited-array image before argument evaluation. It then checks the snapshot,
separate callee copy, source mutation, callee defer, outer sentinel and completed
stack top. Valid short, long, omitted and original-source controls fail image
assertions. A missing restore fails the live top assertion. A valid aliased-frame
control fails the independent-parameter assertion. Empty-parameter and summed
frame-overflow guards use native-valid inputs. Huge layouts are C-emission-only;
they are never built or executed.

The initial setup used a wrong executable path and started no compiler. The
next preflight found invalid `length(a)` syntax; completed earlier cases were
hash-verified and reused, with only unfinished cases rerun using `a.len`.
A direct string literal cannot bind to a fixed array parameter in the frontend;
that invalid input is retained separately. The valid case first constructs a
fixed array from the string. These are not compiler defect claims.

The first native suite found missing expected-warning markers for redundant
casts and reference operators. Only EOF comments were added; all four affected
Wasm modules remain byte-identical and pass both engines. That failed run is
preserved. Old fixed-inline argument and aggregate-array admission guards were
reproduced, then changed to require the supported executions. Variable-array
arguments and array results retain their specific rejection checks.

A read-only native Codex bug search found no confirmed correctness defect. Its
three coverage risks were early inline/callback argument exits, dynamic source
memory identity and reference arrays with active data memories. Separate
native-first and both-engine cases now cover those paths. The compiler source
did not change after the first frozen build.

Runtime storage and byte-copy work scale with the complete parameter images
and the number of simultaneously live snapshots and frames. The storage map
gets a record for each newly admitted array parameter. The mixed-call capture
vector and emission recursion already existed for nominal arguments. No new
guest heap object or compiler field is added. These are static costs and their
correctness reasons, not measured runtime, compiler allocation or physical
memory claims. Joshua's correctness-only directive excludes measurements and
measurement-lease work from this thread.

The final correctness-only suite passes 2,639 Wasm checks, including all forty
complete memory matrix cases. The final native baseline passes 2,144 frontend,
1,048 generated-C and 1,220 TinyCC groups, plus all other baseline groups. All
52 exact comparisons pass. All 576 unchanged parent fixture modules are
byte-identical. The final 78 source/support files and 4,728 validation inputs
match their frozen hashes. The earlier 25-family full run also passed; the final
run includes the four added coverage families and warning-only comments.

The selected compiler SHA256 is
`1ca624dfd88155c05f1d4f1ea187c069f30f154d4ced48751320f0287728d6c3`.
Selected records and raw hashes are in the
[archive manifest](array-arguments/archive-manifest.json). Raw binaries and
complete records remain in `/tmp/goose-wasm-array-arguments-20261108`.
Execution evidence is Linux native plus the configured Node/Wasmtime hosts.
No performance or cross-platform runtime acceptance is claimed. The complete
backend is still unfinished; array results are the next compilation step.
