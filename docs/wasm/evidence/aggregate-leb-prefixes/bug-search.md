# Aggregate unsigned LEB prefix source review

Reviewed revision: `c727452fdf7c585e277b8bb3e19f2a91d4a19836`, branch `feat/wasm-multimemory-backend`. The worktree was clean at the first check.

Scope: read-only review of the proposed admission of nominal `T[varint]` arrays, literal/fill construction with a count-specific prefix, and exact stored copies through InitArrayCopy. No production edits, builds, tests, guests, timing, profiling, lease work, child agents, or Claude use. No new execution evidence is claimed. The supplied AGENTS rules apply; the prior search found no applicable on-disk root/ancestor/src/test AGENTS.md.

## Result

No confirmed valid-input wrong-result, namespace, ABI, or lifetime defect was found in the proposal as stated. It must retain the prefix-specific conditions below. One scope statement needs correction: nominal array equality remains rejected, even though the scalar equality implementation understands LEB widths.

## Requirements and conditional hazards

1. **Do not call fixed DataPrefix on a LEB type.** `ArrayPrefix` returns elements = -1 for IS_VARINT (`src/value_layout.h:31-41`). `DataPrefix(array)` asserts that this value is nonnegative (`src/wasm_codegen.h:156-159`). The current ReserveFreshDataArray calls it unconditionally (`src/wasm_arrays.h:829`). The literal branch must choose `DataPrefix(array, literalCount)`. The dynamic-count branch must reject a LEB type before evaluating the fixed-prefix helper. Removing admission alone leaves an assertion failure reachable on ordinary LEB literals in assertion builds; release behavior would also use a wrong prefix. This is a requirement of the proposal, not an independently reproduced defect in its completed implementation.

2. **Allow three- and five-byte literal prefixes.** The current shape check accepts only 1, 2, 4, or 8 (`src/wasm_arrays.h:830-831`). LEB count 16384 requires three bytes, and sufficiently large memory32 counts can require five. Keep the fixed unsigned shape check only for non-LEB arrays. Apply the full payload extent bound using the actual prefix byte count before multiplying count by stride (`834-839`). Retain the fill count check before uint32 conversion (`876-879`).

3. **Use the same width for reservation and destinations.** Literal/fill construction uses the returned prefixBytes in FreshDataElement and the repeat loop (`src/wasm_fixed.h:297-309`; `src/wasm_arrays.h:880-895`). InitArrayCount emits canonical unsigned LEB bytes (`src/wasm_arrays.h:221-234`), from the same count used by DataPrefix's seven-bit loop (`src/wasm_codegen.h:161-165`). Required boundary images are 127 = `7f`, 128 = `80 01`, 16383 = `ff 7f`, and 16384 = `80 80 01`. Payload offsets must be 1, 2, 2, and 3 bytes respectively.

4. **Route exact-layout stored LEB copies before the fixed dynamic reservation path.** InitArrayCopy captures count and decoded width, bounds count * stride, adds decoded width in i64, checks the sum against UINT32_MAX, then reserves and copies the full image (`src/wasm_arrays.h:487-551`). It copies the source prefix and payload together, so no destination prefix rewrite is required. ArrayLength captures the i32 width before leaving the i64 count on the stack (`197-205`). ReadPrefix returns count plus width (`src/wasm_memory.h:164-203`). Keep the existing fixed-prefix dynamic ReserveFreshDataArray path separate.

## Address, lifetime, and ABI checks

- Size(nominal) calls RequireFixed (`src/wasm_codegen.h:232-238`), so InitArrayCopy does not need a scalar-only size path. ArrayLayout also uses Size(element) (`src/wasm_arrays.h:18-25`).
- ElementAddress captures count and decoded width before index evaluation (`src/wasm_arrays.h:1082-1093`). ElementOffset uses that width, checks the full offset, and preserves the high memory-id bits (`1042-1075`). The three-byte boundary does not depend on fixed alignment.
- By-value nominal iteration admits DataNominalArray, decodes prefix width on each length check, and passes it to ElementOffset before CopyFixed (`src/wasm_arrays.h:1377-1406`). By-reference iteration uses the same selected packed element address (`1407-1411`). No scalar load of a nominal value is added by this admission.
- Storage planning already treats all A_VAR owners as data owners (`src/wasm_storage.h:59-61`), assigns them before initializer calls (`90-108`), and selects concrete or dynamic data memory from the owner plan (`254-258`). Prefix type does not alter these rules.
- InitArrayCopy captures the source before reserving the destination, registers the destination restore in the active declaration scope, and copies with sourceMemory and destination memory proofs (`src/wasm_arrays.h:495-551`). A source array borrowed through a reference keeps a packed address with unknown concrete memory (`61-70`, `99-109`). No memory is inferred from the element type.
- Removing the prefix exclusion does not add a by-value array ABI. RequireCallValue still rejects nonfixed by-value array parameters/results (`src/wasm_codegen.h:130-140`). Ordinary references to these arrays use the existing fat-reference ABI. NoteType follows referenced array types and marks owned data addresses, so prefix admission does not omit this ABI choice (`src/wasm_storage.h:34-43`; `src/wasm_codegen.h:142-148`).
- Fill capture lifetime remains unchanged: ReserveFreshDataArray completes the owner before WithFixedTemporary, which holds the Memory 0 snapshot around the complete loop (`src/wasm_arrays.h:880-898`). Exiting field initializers and scope restores retain the previously reviewed behavior.

## Existing limits that remain

- **Nominal array equality is unsupported.** ArrayEquality rejects nominal elements explicitly at `src/wasm_arrays.h:1185-1186`. Trigger: equality of two stored `S[varint]` arrays after this admission. The LEB-aware equality loop applies to scalar elements only. This is a pre-existing target limit, not a new wrong-result regression. Do not report nominal LEB equality as supported without a separate change.
- Mutation of variable arrays is rejected before count stores (`src/wasm_arrays.h:1138-1139`). Growable/runtime-limited nominal arrays do not become admitted merely by widening DataNominalArray, which still requires A_VAR.
- Nonfixed struct fields remain rejected (`src/wasm_support.h:31-36`), and fixed nominal admission still rejects nonfixed/root/frame layouts, relative references, zero-stride elements, and unsupported leaf types (`48-65`, `89-101`). An ordinary reference field can point to a LEB nominal array without changing its own fixed storage representation.
- Existing fixed/count-prefix conversions use the count-specific prefix or a decoded source width (`src/wasm_arrays.h:312`, `398-413`, `446-467`, `473-479`). Their existing target admission limits still apply. Nonfixed block/if value transport and general aggregate value-producing matches remain outside this narrow extension.

## Parent execution targets

Use complete owner images and stack-top checks for literal, fill, and exact stored copy at 0, 127, 128, 16383, and 16384. Include a three-byte prefix with a packed odd stride, a nominal enum payload, nested fixed fields, retained ordinary reference targets, globals, and runtime-selected memory identities. Exercise indexed reads/writes, by-reference and by-value iteration, copies through references, repeated calls with a live sibling owner, and early exits/defer during fill evaluation. Check fixed-to-LEB, static-limited-to-LEB, and LEB-to-fixed-prefix conversions within the already admitted target types. Keep unsupported equality and nonfixed owning fields as rejection checks. None of these cases were executed by this reviewer.

## Source-only cost assessment

Literal/fill storage becomes `LEB width(count) + count * stride`. The prefix-width calculation grows with the number of seven-bit groups, at most five for an admitted memory32 literal count. Literal prefix emission adds one byte store per group. Stored copies and indexed/iteration accesses use the existing decoder; its work grows with encoded prefix width. Exact copies reserve one full destination image and do not add a snapshot. Fills retain one element-sized Memory 0 snapshot. No new managed allocation mechanism or per-element temporary allocation is required by the proposal. No runtime, allocation, compiler-time, or memory measurements were run.
