# Read-only fixed-result bug search

Provider: native Codex worker, gpt-6.1-sol, high reasoning.
Task: /root/fixed_results_bug_search. No edits, builds, guests, timing or lease work.
Scope: uncommitted fixed-result code before the later builtin-dispatch narrowing,
21 fixture families and both result-check helpers. Parent 69ed07e4.

No confirmed correctness defect found.

Checked hidden result parameter order and local indexes; incoming destination
checks and nested offsets; direct, forwarded, inline and callback construction;
packed-data landing lifetime; result-before-defer cleanup and frame restoration;
block/conditional construction; relevant storage, type-checking, optimizer and
native callback code.

Coverage gaps, not confirmed bugs: explicit early inline nominal returns, and
callback nonlocal nominal returns during nested aggregate construction. The
parent added separate native-first inline_early and callback_exit fixtures after
this report. Real self-recursion was added too.

Unread: expected-output files, raw validation records and unrelated source.
The later narrowed builtin dispatch and added tests were not a worker re-review.
