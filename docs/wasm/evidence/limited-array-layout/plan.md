# Static limited-array conversion

Parent: 671f86b2406eaf9e32f9e08e99d3404d032dc1a9.
Candidate: corrected build02, 85-file build snapshot, final compiler identity 875bd697.
Purpose: correctness only. No timing or measurement lease.

Use the existing fixed-place and checked-owner services. Copy only live source
elements, with source and destination count-prefix offsets kept separate.
Require a smaller destination's count guard before payload/count writes.
Preserve source evaluation, destination capture and temporary owner lifetime.

Thirty-two native-valid rejecting parent cases, 64 O0/O2 positive pairs,
Memory 0/data/wide/failure observers with 32 validated controls and healthy
runs, full Wasm correctness, native baseline, 52 exact comparisons, unchanged
parent module identities, source and staged archive checks. Invalid fixture
attempts remain preserved and are not production defects.

Variable/growable/data-prefix destination conversion is separate work. Its
next native-valid failures are saved outside this stage. No source or validation
input changed during the full-suite run.

The initial code-9 capacity guard and filename-matching assertion are preserved.
The exact-message regression fails in reason01 and passes in reason02. The
obsolete full-correctness01 was interrupted and is not validation. Final source
and tests are frozen again for full-correctness02/native02/exact02.

Final verifier01 had a snapshot-inventory KeyError: build02 includes seven
tracked runtime sources beyond the initial 78. The verifier checks all seven
against the parent commit; original failure and helper are retained.
