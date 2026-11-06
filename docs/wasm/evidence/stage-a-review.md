# Independent ABI review

Base: upstream/master 7b90f91d91845f4ef1712e16ed053f395e4e6e1c.
A separate read-only Codex worker inspected the complete initial ABI document
against the specification and relevant C lowering. It found no confirmed defect.
It identified open details for packed pointer widths, Memory 0 prefix/frame
ownership, host reentry, the exclusive 4 GiB top, and worker global snapshots.
The document now states those rules. Full recursion, serialization, OS/thread
cleanup, and probe harnesses were outside that worker's complete inspection.
The parent separately ran the multi-memory/EH capability probe under Node
24.22.2 and Wasmtime 49.0.3 and validated it with wasm-tools 1.262.0.
This is an ABI review, not proof of full backend support or performance.
