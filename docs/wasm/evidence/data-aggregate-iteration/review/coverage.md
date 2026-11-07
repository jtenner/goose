All 42 primary files were read in full. No primary lines remain unread.

The table lists the inspected source ranges. Raw and binary limits, with every path, are in [unread-inputs.json](/tmp/goose-wasm-data-iteration-review-20261107/review/unread-inputs.json). Hash-only checks do not establish binary behavior.

| Class | File | Inspected lines | Unread lines |
| --- | --- | --- | --- |
| primary | docs/wasm/evidence/data-aggregate-iteration.md | 1-112 | None |
| primary | docs/wasm/measurements.md | 1-243 | None |
| primary | docs/wasm/status.md | 1-319 | None |
| primary | src/wasm_arrays.h | 1-1042 | None |
| primary | test/expected/wasm_data_aggregate_iteration_callbacks.out | 1 | None |
| primary | test/expected/wasm_data_aggregate_iteration_checkpoint.out | 1-6 | None |
| primary | test/expected/wasm_data_aggregate_iteration_cleanup.out | 1-6 | None |
| primary | test/expected/wasm_data_aggregate_iteration_control.out | 1-2 | None |
| primary | test/expected/wasm_data_aggregate_iteration_defaults.out | 1 | None |
| primary | test/expected/wasm_data_aggregate_iteration_enum_image.out | 1-4 | None |
| primary | test/expected/wasm_data_aggregate_iteration_enums.out | 1 | None |
| primary | test/expected/wasm_data_aggregate_iteration_fields.out | 1 | None |
| primary | test/expected/wasm_data_aggregate_iteration_inline_image.out | 1-3 | None |
| primary | test/expected/wasm_data_aggregate_iteration_paths.out | 1 | None |
| primary | test/expected/wasm_data_aggregate_iteration_reference_targets.out | 1 | None |
| primary | test/expected/wasm_data_aggregate_iteration_refs_packed.out | 1 | None |
| primary | test/expected/wasm_data_aggregate_iteration_values.out | 1 | None |
| primary | test/expected/wasm_data_aggregate_iteration_walk_data.out | 1 | None |
| primary | test/expected/wasm_data_aggregate_iteration_zero_control.out | 1 | None |
| primary | test/wasm/wasm_data_aggregate_iteration_callbacks.goose | 1-7 | None |
| primary | test/wasm/wasm_data_aggregate_iteration_checkpoint.goose | 1-11 | None |
| primary | test/wasm/wasm_data_aggregate_iteration_cleanup.goose | 1-17 | None |
| primary | test/wasm/wasm_data_aggregate_iteration_control.goose | 1-11 | None |
| primary | test/wasm/wasm_data_aggregate_iteration_defaults.goose | 1-6 | None |
| primary | test/wasm/wasm_data_aggregate_iteration_enum_image.goose | 1-6 | None |
| primary | test/wasm/wasm_data_aggregate_iteration_enums.goose | 1-12 | None |
| primary | test/wasm/wasm_data_aggregate_iteration_fields.goose | 1-15 | None |
| primary | test/wasm/wasm_data_aggregate_iteration_inline_image.goose | 1-6 | None |
| primary | test/wasm/wasm_data_aggregate_iteration_paths.goose | 1-23 | None |
| primary | test/wasm/wasm_data_aggregate_iteration_reference_targets.goose | 1-21 | None |
| primary | test/wasm/wasm_data_aggregate_iteration_refs_packed.goose | 1-8 | None |
| primary | test/wasm/wasm_data_aggregate_iteration_values.goose | 1-13 | None |
| primary | test/wasm/wasm_data_aggregate_iteration_walk_data.goose | 1-10 | None |
| primary | test/wasm/wasm_data_aggregate_iteration_zero_control.goose | 1-6 | None |
| primary | test/wasm_backend.py | 1-643 | None |
| primary | test/wasm_data_iteration_admission.py | 1-55 | None |
| primary | test/wasm_data_iteration_checks.py | 1-74 | None |
| primary | test/wasm_data_iteration_footprint.py | 1-47 | None |
| primary | test/wasm_data_iteration_global.mjs | 1-34 | None |
| primary | test/wasm_data_iteration_owner.mjs | 1-86 | None |
| primary | test/wasm_memory_snapshot.mjs | 1-4 | None |
| primary | test/wasm_memory_snapshot_checks.mjs | 1-19 | None |
| context | src/wasm_support.h | 1-108 | None |
| context | src/wasm_codegen.h | 1-225, 345-465, 918-963, 1000-1188 | 226-344, 466-917, 964-999, 1189-1295 |
| context | src/wasm_fixed.h | 1-526 | None |
| context | src/wasm_storage.h | 1-225 | None |
| context | src/wasm_memory.h | 1-243 | None |
| context | test/wasm_reference_abi.mjs | 1-46 | None |
| context | test/wasmtime_host.py | 1-169 | None |
| context | scripts/run_wasm.mjs | 1-153 | None |
| context | test/wasm_iteration_checks.py | 1-143 | None |
| context | test/wasm_data_aggregate_checks.py | 1-74 | None |
| context | src/ast.h | 1275-1340, 1694-1715 | 1-1274, 1341-1693, 1716-2967 |
| context | test/wasm_reference_abi_controls.py | 1-50 | None |
| context | docs/goose_spec.md | 1390-1406, 2384-2440, 3037-3072 | 1-1389, 1407-2383, 2441-3036, 3073-5270 |

{
  "primary_total": 42,
  "primary_fully_read": 42,
  "context_total": 13,
  "context_fully_read": 10,
  "context_partly_read": 3,
  "raw_total": 6636,
  "raw_text_not_fully_read": 3543,
  "binary_hash_only": 1728
}

Raw status and structured parsing are recorded separately from full text reads. Packet hashes, manifests, and file listings do not count as source inspection. Unread binary content includes all modules, native executables, compiler bytes, and saved memory images.
