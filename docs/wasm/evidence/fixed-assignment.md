# Exact fixed aggregate assignment

Existing fixed structs, enums and variants can now be assigned by exact stored
layout. The compiler captures the target before evaluating the source and uses
the existing checked cross-memory byte-copy service. It does not reconstruct
fields or change shallow reference targets. Local/global owners, fields,
elements and reference pointees share this path. Self-copy is supported.

The source must already have an addressable complete fixed image of the exact
same type. The frontend's lifetime and read-only checks remain active. This
does not admit whole arrays, layout adaptation, constructors, aggregate-valued
calls or results. A checked ordinary reference result can name an existing
source. Relative and nonfixed layouts retain their earlier guards.

Before the fix, eighteen native O0/O2 cases passed and the same source failed
with the exact whole-aggregate Wasm assignment diagnostic. The repaired cases
agree in Node and Wasmtime. They cover packed fields, copied references,
multiple memories, dynamic source/target identities through parameters,
left/right evaluation order, a source call that rebinds the target's parent,
enums, variants and empty values.

The full Memory 0 observer seeds valid inactive enum bytes in an existing
source, then checks complete destination images and adjacent objects. It
detects validated short, long and omitted copies at the named image assertion.
It does not claim deterministic initialization of inactive padding. The eight
healthy/control groups pass. Completed-owner checks are part of the permanent
fixtures. The source escape from an inner scope remains a frontend rejection.
A valid outer-owner reference copy survives the inner record's scope and a
later allocation in native code and both engines.

The integrated correctness-only suite passes 1,481 groups, including all forty
Memory 0/data matrix cases. The native baseline passes 1,824 frontend groups,
888 generated-C runs, 1,060 TinyCC runs and all other baseline groups. All 52
exact comparisons pass; 294 unchanged-source modules are byte-identical.
Compiler SHA256 is
`9f7850e52ab34ed351e0567261c0f26903770af44559f956f29e5c9625d300a4`.
The source snapshot was captured after the completed build; no source edits
occurred during that build. Source and validation hashes match before and
after the integrated runs.

The final lifetime fixture and lifetime-policy assertion were added after the
integrated run. The unchanged compiler passes their separate native,
Node/Wasmtime, completed-owner and five-group policy checks. No second full run
is claimed for those test-only additions.

Raw records are retained under `/tmp/goose-wasm-fixed-assignment-20261107`.
Selected identities, commands, statuses and results are in
[fixed-assignment](fixed-assignment/archive-manifest.json). No measurement,
timing acceptance or lease rotation is part of this work.

Constructor replacement is the next compilation block. The native schedule
constructs a plain fixed RHS before storing it. It needs a scoped Memory 0
temporary and ordered cleanup; deleting the constructor guard or writing each
field directly into the target would change initializer/default observations.

The later [constructor assignment increment](constructor-assignment.md) resolves
that specific constructor block with a checked temporary and ordered cleanup.
The results above remain the original fixed-copy checkpoint.
