# Aggregate data fill source review

Revision: `d238b3a64b8d5a052cc48058854cf888260995fb`, branch `feat/wasm-multimemory-backend`.

Scope: source review of the proposed fixed nominal data-array fill extension. No production edits, builds, tests, guests, timing, profiling, lease activity, Claude use, or child agents. The worktree was clean when checked. No applicable on-disk AGENTS.md was found in the repository root, ancestors, src, or test; the supplied instructions apply.

## Result

No confirmed valid-input wrong-result or memory-lifetime defect was found in the proposal as stated. The implementation does not yet exist: `src/wasm_arrays.h:873` rejects every aggregate data fill. Thus this report does not claim execution evidence or a proven fix.

## Requirements to retain

1. **Check the full count before narrowing it.** `ReserveFreshDataArray` takes `uint32_t literalCount` (`src/wasm_arrays.h:821-823`). Its checks at lines 834-839 see only that narrowed value. A fill count starts as signed 64-bit, after the type checker replaces it with an IntLit (`src/typecheck_nodes.h:230-238`). For `S[u64]`, the front-end count check does not impose a 32-bit bound (`src/typecheck.h:2037-2044`). If the new caller directly casts count `4294967296` to uint32_t, the helper sees zero and reserves only the prefix. This is a conditional implementation risk, not a defect in the current rejection path. Check `count < NoLocal` or the stricter memory32 extent bound while count is still uint64_t, then pass it to the helper. The positive stride and positive prefix make every valid memory32 reservation strictly smaller than NoLocal.

2. **Evaluate and capture fillval once, including count zero.** This is explicit in scalar fills (`src/wasm_arrays.h:733-742`) and fixed aggregate fills (`src/wasm_fixed.h:825-829`). The C backend freezes the value before its repeat loop (`src/codegen_construct.h:959-1002`, `1251-1279`). WithFixedTemporary outside the runtime loop preserves this rule. A zero-count early return before the temporary would change observable side effects and exits.

3. **Keep the complete data reservation before fill evaluation.** `ReserveFreshDataArray` checks extent, reserves the full owner, registers its restore, and writes the owner slot before returning (`src/wasm_arrays.h:829-867`). The storage walk assigns declaration owners before visiting initializers (`src/wasm_storage.h:90-108`); calls inside fillval therefore get a stack offset above the live owner (`169-171`). No storage-plan extension is needed for one fill evaluation. Do not move owner reservation inside the loop or after evaluation.

4. **Keep the snapshot scope around the whole consumer loop.** `WithFixedValue` reserves Memory 0 bytes, registers a cleanup action, constructs the value, calls the consumer, then restores the temporary (`src/wasm_fixed.h:140-164`). This keeps the image live until every CopyBytes is done. Returning, breaking, or continuing inside an initializer calls Cleanup through the active scopes (`src/wasm_codegen.h:453-464`, `955-964`). `ConstructFixed` also handles a void/exiting initializer first (`src/wasm_fixed.h:912-915`, `1095-1098`), so a later emitted copy is unreachable. The proposed consumer must not store the temporary address for use after WithFixedTemporary returns.

5. **Retain the packed namespace and extent proof.** Use the fresh image's packed address and its actual memory proof. For runtime-selected memories, keep `memory == -1`; do not infer a memory from element type. CopyBytes then selects CopyFromFrame for a Memory 0 snapshot and a packed data destination (`src/wasm_arrays.h:243-260`). Compute destination = fresh packed base + prefix + position * stride, with position bounded by the same full count used for reservation. The complete reservation proves that this addition cannot carry into the memory id. Do not use a uint32 loop index as a FixedPlace constant offset or drop the namespace bits.

## Excluded cases and remaining limits

- Relative references and `self` do not refute byte copying in this scope. Admission rejects relative references (`src/wasm_support.h:50-53`); `self` requires such a reference (`src/typecheck_exprs.h:3178-3185`). C's per-element relative-reference construction is required outside the proposed scope, but not within it.
- Fixed nominal elements can contain ordinary absolute references. Copying their stored reference bits preserves the target, as the existing fixed fill reference fixture expects (`test/wasm/wasm_aggregate_construction_refs.goose`). No new managed-root mechanism was found in this stack-based Wasm path. The frame temporary has its own ordered restore and does not own the referenced target.
- Existing aggregate expression support remains a limit. ConstructFixed supports blocks, if expressions, direct calls, inline blocks, literals, and stored values. Aggregate MatchExpr, EarlyBlock, and LoopExpr do not get a new construction protocol from WithFixedTemporary (`src/wasm_fixed.h:1155-1163`, `1210-1229`; `496-506`; `440-460`). These are pre-existing target limitations, not confirmed regressions caused by this extension. Do not claim all nominal-valued language expressions are newly supported without separate checks.
- Nonfixed fields, root structs, frame objects, relative references, zero-stride elements, LEB prefixes, capacity constructors, and default constructors remain excluded by the task or admission rules (`src/wasm_support.h:23-25`, `31-36`, `62-65`, `89-101`).

## Checks for parent execution

Exercise nonzero and zero fills with side effects; literal, named, block, conditional, direct and inline aggregate producers; all four fixed unsigned count prefixes; nested scalar/nominal fixed fields; ordinary references to frame and data targets; enum/variant payloads; both concrete and runtime-selected data memories; globals; early return, break, continue, and defer paths. Check the live Memory 0 temporary and full data-owner image, then verify both stack tops after completion. Use independent instances and repeated calls with retained sibling owners to catch namespace or restore errors. For u64 count overflow, include a count above UINT32_MAX so a narrowing bug cannot pass unnoticed.

## Source-only cost changes

The extension adds one Memory 0 reservation of max(1, element stride), active for evaluation and the copy loop. Data storage is prefix + count * stride. Runtime copy work grows with count * stride. The runtime loop avoids generated instruction count growing with the fill count. No timing, allocation measurement, compiler-time measurement, or memory benchmark was run, as requested.
