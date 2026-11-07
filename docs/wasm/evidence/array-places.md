# Memory-aware array places

Status: implementation, compatibility, private regression and the 1,036-check full Wasm suite passed. The native baseline and all 52 exact comparisons passed. Independent Astra review found no confirmed production defect. Its archive finding is resolved below. This is a Stage D service increment, not full backend completion.

## Scope

The compiler now carries array image layout, header/payload memory, bounds, origin, and captured count/prefix facts in `ArrayPlace` and `ArrayView`. `ElementPlace` carries the selected element type and memory while retaining the old operand-stack address transport. Constructors, copies, byte/fill paths, counts, indexing, mutation, equality, walks, loops, print snapshots and fixed field places use these services.

The current borrowed-array transport and source admission stay unchanged. Inline array references and growable owner headers keep their existing thin ABI. Prefixed data borrows keep the existing packed ABI. This increment does not admit general aggregate values in data memory, by-value calls/results, or other pending layouts.

Direct known-memory and checked dynamic-memory copy routes share explicit source and destination places. Caller-supplied capture locals retain the parent emission order. A constructor-scoped frame-slot pointer retains the exact old direct address sequence; no stored place outlives that caller slot in the current implementation.

## Exact source and compatibility

Parent: commit `b04500bbfcf55d935f6caa4d895cfa5b918edf2c`, compiler SHA256 `c9519e59d47ea996b84d249fee688704bfab0ed49cf5c1ef844e7daf3bdd60d2`.

Corrected compiler: SHA256 `5b68b041c3aba5c6bd6a6fa7e96a0b5a8aa5cc5558761b56efa5d83cacb1599a`, frozen in build02 with a checked source manifest. All 226 accepted parent module pairs, stdout and stderr are byte-identical. This shows emitted-module compatibility; it does not measure compiler CPU/RSS or prove execution of new private forms.

## Failing-first private contract

The synthetic helper forms a runtime-limited byte image in memory 2 at base 16 plus image offset 3. Capacity and length are at image offsets 0 and 4; elements start after an eight-byte prefix. Element zero must be packed `(2 << 32) | 27`, or 8589934619.

With the initial D-place source, both Node 24.22.2 and Wasmtime 49 returned 27. The module validated first. The thin-to-packed element conversion discarded the known nonzero memory number. The correction inserts those memory bits after widening the low address. The Memory 0 path is unchanged. This form is accepted by the new private service but is not emitted by current source lowering, so the evidence does not establish a source-program regression.

The failed module, both engine streams/statuses, source snapshots and source diff remain under probes05. Probes06 validates and passes all unchanged assertions in both engines after the correction. Test-source hashes match the failing attempt exactly. The tests also cover address edges, offset overflow, wrong-memory narrowing, count/capacity load-store, concrete/dynamic copy direction, overlap, constant-source copies, invalid memory IDs and out-of-bounds copies with full memory snapshots.

## Preserved setup errors

Probes01 omitted the real compiler header order. Probes02 still lacked native AST pass definitions. Probes03 then lacked the normal shader-wrapper link dependency. Probes04 built but appended an extra function-end instruction that the module writer already adds. No engine result was obtained in those attempts. Each raw failure remains separate. The final helper uses the real header order and existing normal-build shader library, without test stubs or production link changes.

## Pending checks and costs

The corrected private regression and full 1,036-check Wasm suite passed, with source/executable/input identities checked before and after. The full native baseline passed with explicit TinyCC setup and before/after provenance checks. Its saved output lists existing layer/GPU/platform and unsupported-JIT skips. All 52 exact generated-output/report/diagnostic comparisons passed with before/after provenance checks. Independent Astra review found no confirmed production defect. Its archive finding is resolved below. No build, execution or review result is inferred from a prepared command.

The place facts use value structs; no new per-access heap wrapper or per-element vector is introduced. Host copies of those facts and layout queries can still cost compiler work. Existing guest modules remain identical, but that is not a measured runtime gain. The queued measurement handoff compares parent and final frozen candidate compiler CPU/wall time, allocations and RSS across shared scalar/reference/aggregate callers, large literals, nested paths, concrete/dynamic identities, copies, loops, equality and print snapshots. Fresh coordinated scope, host controls and an exclusive lease are required. No old timing grant is reused and no physical-memory or speed improvement is claimed.


## Saved records

- [Frozen build identity](array-places/build02/build-identity.json),
  [source hashes](array-places/build02/source-hashes.json), and
  [226 module pairs](array-places/build02/prior-modules.json).
- [Failing private contract](array-places/probes05/confirmed-contract-error.json),
  [Node failure](array-places/probes05/node.stderr),
  [Wasmtime failure](array-places/probes05/wasmtime.stderr), and
  [passing-after record](array-places/probes06/regression-after.json).
- [Full Wasm output](array-places/full-wasm01/full-wasm01.stdout),
  [native output and skips](array-places/native-baseline01/native-baseline01.stdout),
  and [52 comparison output](array-places/compatibility01/compatibility01.stdout).
- [Source cost audit](array-places/source-cost-audit.json),
  [setup attempts](array-places/setup-attempts.json), and
  [archive hashes](array-places/archive-manifest.json).

Complete raw helper/module/native artifacts remain under
`/tmp/goose-wasm-array-places-20261107`. Successful copied files have manifest
hashes; raw failed attempts remain separate. Validation is Linux native plus
Node/Wasmtime on this host, not native cross-platform runtime evidence.


## Independent review and archive repair

[Astra's report](array-places/review/report.md) found no confirmed production
correctness or design defect. It found that the linked build-identity JSON file
was omitted from the index by the broad `build-*` ignore rule. The exact saved
file is now explicitly staged. All 81 archive-manifest destinations were read
from the index and matched their recorded hashes. No production or test file
changed after review, so this archive repair needs no suite rerun. See
[resolution](array-places/review-resolution.json) and
[index checks](array-places/archive-index-checks.json).

The review inspected all 92 original changed files. Six context files were
partly read, and 3,235 supplemental raw files or partial diagnostics have unread
content. Binary inspection covered identities, sections and the changed helper
body; it was not a full instruction audit or new execution. The complete
[inspection inventory](array-places/review/inventory.md) and unread-file records
retain those limits. The reviewer directly compared all 226 parent module pairs
and all 52 older-checkpoint output pairs. The 1,036 suite count denotes check
groups, not distinct programs; the 226 module pairs cover 113 fixtures at two
optimization settings. The 52 older-checkpoint pairs comprise 34 native and
18 Wasm output/report comparisons. None is a universal compatibility proof.

Compiler CPU, allocation, RSS and physical-memory acceptance remain open.
Larger place values and existing walk-vector elements can add work that grows
with constructor size, type complexity and path depth. The queued handoff in
[measurements](../measurements.md) is not a measured acceptance result.
