# Read-only fixed array result bug search

Native Codex worker gpt-6.1-sol/high, /root/array_results_bug_search.
No edits/builds/tests/guests/measurements or other workers.

No confirmed reachable correctness defect found.

Checked result ABI/signatures/callee/direct/inline/discard paths, reference ABI,
copy-before-defer, assignment landing, three changed headers and both initial
result-check helpers; all first25 fixtures/expected outputs; relevant storage,
layout, reference, copy and cleanup APIs. No assigned files unread.

Coverage risks, not confirmed defects: add returned array-reference copy/discard
control; add focused nested block/conditional data-field image checks.
Parent added both after this report. The reference control already compiled
without a code change; nested models inspect complete Memory 0/data images,
owner state and valid mutated stores. The later data observer was not a second
worker review. No production source changed after the frozen build.
