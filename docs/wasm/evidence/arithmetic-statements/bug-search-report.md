# Fixed arithmetic statement bug search

Read-only native Codex searches confirmed two existing compile gaps: AssignFixed rejected normalized compound operators, and Statement did not send discarded fixed unary minus through the checked temporary service. Parent-first native-valid reproductions are recorded separately.

The prototype itself checked compound tokens after Statement had already normalized them. The search identified both guard mismatches. The first prototype build was preserved; its array rejection was actually recorded before the two guard corrections. The corrected build passed the same case and all focused paths.

The follow-up search found no further confirmed defect in captured lvalues, scalar capture before stores, old-value copies before effectful RHS calls, RHS reference results, direct ordered leaf writes, early return/continue cleanup, empty-array RHS effects or data-memory offsets. No worker edits, builds, guests or timing were run.
