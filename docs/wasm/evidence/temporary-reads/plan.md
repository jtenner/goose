# Scoped reads from fixed temporaries

Correctness only. No timings, performance gate, measurement lease or sweep coordination.

Parent: 28fc70af256fab83ac630ee9bd27045972d839b9.

Read scalar fields, array elements, lengths and capacities from fixed producers while the owning Memory 0 reservation is live. Save scalar/contained-reference values before cleanup. Project nested fields/elements and copy aggregate images inside that scope. Do not return references into temporary storage.

Native-first cases cover direct/inline/callback/global/block/conditional/default/literal/copy roots, single evaluation, early return/break/continue, nested reference projections, scalar FP bits, contained reference identity/null tests, and projected aggregate construction/assignment.

The complete image observer checks returned array and index scratch while both are live, sentinel bytes, index mutation and restored tops. Valid early release, missing restore and wrong image controls must fail named assertions.

Preserve build01 compiler error, focused-extra01 scope correction, parent-more01 output-expectation failure, and focused-final01/controls-final02 diagnostic mismatches. Build04 uses the narrow contained-reference dispatch fix after reference-failing01 reproduces it. Full checks and identity validation gate commits.
