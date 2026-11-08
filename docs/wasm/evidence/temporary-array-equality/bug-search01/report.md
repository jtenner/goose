Read-only native Codex bug search. No worker build, test, edit or timing run.

First pass inspected the value-snapshot path. No confirmed defect found. It requested limited-array lengths/inactive bytes, reference-slot rebinding, borrowed left roots, early control exits, short circuit and FP cases. Those native-first and both-engine cases are in the final fixture set.

Second pass inspected the added whole-comparison-view path in build02. No confirmed defect found. The path requires both frontend cmpview SliceExprs, absent bounds/from-end flags and InlineArray roots. It captures left address/length before RHS, retains temporary roots, reads elements afterward, and saves the result before cleanup. It requested growing limited length, reference-root rebinding, projected temporary roots, reversed types and early exits. Native-first tests were added for these cases and pass in both hosts.

This is a source bug search, not performance or cross-platform acceptance. The final full-suite status is recorded separately.
