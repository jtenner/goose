# Read-only temporary-borrow bug search

Native Codex worker: GPT-6.1-Sol, high reasoning. No builds, guests, tests, edits, timings or profiling.

No confirmed correctness defect found in the source delta. Inspected CallValue, FixedCallArguments, TemporaryBorrowSource, ScalarBorrowResult, construction, address capture, cleanup, return/continue, storage planning, reference fields, array references and frontend lifetime checks. The worker found that owners remain active through later arguments and the callee; the result is captured before cleanup; return/continue include the active temporary scope. Frontend lifetime checks reject storing a borrowed pointer into caller storage that outlives the owner.

Scope note: the exact-pointee bridge also admits struct and fixed-array subobjects, beyond the scalar-reference examples in the brief. The positive matrix includes nested struct fields, nominal array elements and fixed-array fields. It also covers explicit address forms, later return/continue/break, mixed fixed-value/borrowed arguments, stored reference fields and data memories. No compiler edit was needed for this note.

Limits: source-only bug search. No independent execution or performance assessment. The parent's later recorded compiler and guest checks supply execution evidence. No general statement-lifetime, returned-reference, callback or inlined-call support is claimed.
