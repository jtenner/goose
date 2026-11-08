# Read-only array argument bug search

Native Codex worker gpt-6.1-sol/high, /root/array_arguments_bug_search.
No edits/builds/tests/guests/timing/leases or other workers.

No confirmed reachable correctness defect found.

Checked shared FixedParameter policy/admission; direct/inline/callback plans and
copies; fresh proofs, order, early cleanup, nested scratch; scalar/nominal results;
Memory 0/data memory copy dispatch; both helpers, all25 fixture families and
expected outputs; relevant support/layout/array/optimizer/type-checker source.
No assigned files unread.

Coverage risks, not confirmed defects: direct early exits lack matching inline
and callback cases; data-source field case does not explicitly use a dynamic
source identity; reference array case does not combine active data memories.
The parent prepared separate native-first tests after this report.
