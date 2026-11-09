# Symbolic fixed temporary and protected destination plans

Parent: d53da7837bdeaba05f58488a69458e04aec959d0.
Scope: Stage C correctness only. Source admission, source ABI, frame layout and emitted instructions are unchanged.

The storage pass records fixed temporary sites with their stored types and function owners. Fixed argument adaptation and destination snapshots can request a type different from the source expression. Each fixed assignment also records its checked assignment node, destination type and function. The emitter binds those records before a temporary reservation or a protected value copy. Existing complete-span checks and ordered frame restores remain active. Nested assignments save and restore the active protection record.

Nonfixed declarations use the same captured array source-type rule during planning and emission. This includes arithmetic operands and fixed or limited tails inside converted blocks and branches. The rule is requested for the declaration initializer, not for every subtree.

No guest instruction, runtime field, public signature or native backend changes are intended. The compiler adds private maps and per-site records. Their storage grows with the relevant checked AST sites and the types required at each site. This is a source-level cost statement, not a measured compilation or memory result. No measurements, timing or profiling are part of this checkpoint.

Validation pending: final full correctness suite and 52 exact comparisons. Final compiler ea81b203cb500f0c40d763805705abe00ff8a7f15e67785f973db31006157d10 emitted all 2,044 existing O0/O2 fixture modules byte-identically to executed parent records.

Preserved attempts: build01 failed due an unqualified shared layout comparison. Build02 passed its private checks but an admission scan found 110 converted-array variants missing their underlying fixed source record. Those failures are planner defects in this uncommitted increment, not new source-language limitations. The final source shares the source-type rule and passes the complete byte comparison. Original compiler, source snapshots, commands, stderr and exits remain separate.

The backend is not complete. Remaining Stage C work includes nonfixed temporary owners, remaining compound lifetime events and general thin-reference propagation. The existing Stage D limits remain, including aggregate array equality and nonfixed values. Stages E and F follow in the owner-directed order. Stage F is in scope. No measurements are authorized.
