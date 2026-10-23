# Deferred standalone analysis state

This audit covers the `NeedsCaller` rollback in `TypeCheck::Checkpoint`.
It is separate from recovery after a diagnosed error. A deferred helper has
no surviving call path, so it cannot leave new writable-reference evidence or
proof obligations on globals. Earlier real roots' obligations must survive,
including their original source locations.

`EnvRead` is a call-replay/flow record, not a complete variable snapshot.
`DeferredState` therefore journals a complete preexisting `VarDef` by value
before its **first write** in a root and restores it into the **same object**
on deferral. It does not enumerate earlier roots' variables or types at entry.
All 51 current members are accounted for below. A successful root commits
normally; a diagnosed failure follows the ordinary recovery path.

`Ast::varserials` and `detailserials` record allocation order independently of
analysis records and usable registries. They are populated only by `NewVarDef`
and `NewDetail`, are never recycled, and include quarantine ownership. The
root records their boundaries in O(1). `Writing` logs only older variables and
array details. New objects keep their checked metadata for diagnostics and
editor queries after quarantine; rollback does not reset them. In particular,
`ResetLocal` and copying a shared detail cannot overwrite the allocation identity.

| Members | Writers and lifetime | Deferred rollback |
|---|---|---|
| `name`, `line`, `type` | `NewVar`, `CheckVarDecl`, parameter/class-root setup. Declaration identity and concrete type pointer. | Restore the complete old record. Preserve object identity and earlier locations/types. Mutable type pointees are handled separately below. |
| `isvar`, `copybind`, `isglobal`, `isparam`, `resulttemp`, `istemp`, `reusable` | Declaration, iteration/match binders, parameters, temporary and reusable-pool setup. Normally unchanged for old globals. | Restore old flags, never synthesize new declaration properties. |
| `ownerspec`, `depth` | Local/parameter/class-root construction and loop/match bindings. `ResetLocal` reuses local identities across passes. | Restore old ownership/depth. Preexisting stale specialization bodies are not rewritten in a deferable root. |
| `nonneg`, `nonnegfrom` | `CheckVarDecl` records a let initializer and its source chain. | Restore the earlier value facts and links. |
| `constlit`, `constuns`, `constval`, `constnot`, `constflt`, `constfval`, `constfrom` | `CheckVarDecl` records integer/float initializer facts and alias chains. | Restore every value, signedness, adaptation and source flag together. |
| `markof` | `CheckVarDecl` recognizes a let bound to an array length. | Restore the original length-path identity. |
| `classfrom`, `poolclass`, `classpool` | Parameter/class setup and recursive pool validation. | Restore the prior root/pool classification. |
| `growshrink`, `gsvia`, `gselems`, `classreach`, `onearray` | Parameter/class setup and reachable-storage analysis. | Restore all class bounds and their vectors, not just the root pointer. |
| `heldslice`, `heldholder` | Parameter view/holder construction and slot-store analysis. | Restore the previous view/holder links. |
| `ref`, `refrootknown` | Binding/rebinding, `ReplayEnvExits`, reference/slot stores. `ref` includes root alternatives, exactness, writable/reusable/byte-view and other provenance bits. | Copy/restore the whole value, including all nested vectors and flags. |
| `contents`, `contentbyteview` | Holder/literal binding, `AddContents`, `RecordStore`, mapped callee stores and slot stores. | Restore all old alternatives, unknown state and byte-view evidence. |
| `unsized`, `unsizedorigin` | Literal-parameter and function-value argument setup. | Restore the earlier literal adaptation identity. |
| `assigned`, `maybeassigned`, `narrowed` | Declaration, assignment, branch/loop flow, exits and call replay. | Restore old flow; the enclosing checkpoint also restores its ordinary root-entry flow. |
| `captured` | `LookupVar` discovers lexical capture; `ResetLocal` deliberately preserves it across passes. | Preserve the value at transaction entry; discard captures discovered only by the discarded check. |
| `nonneguse` | `RelyOnNonneg` records the first signed/u64 comparison relying on a let's nonnegative initializer. | Restore the old proof/use location, including null when no earlier root relied on it. |
| `markuse` | `ResizesToMark` records a balanced resize. It requires a let owned by the current activation, so it normally touches new transaction-local variables. | Restore the old mark if an old variable is touched; retain marks across passes inside the same successful check. |
| `constuse`, `constwhat` | `RelyOnConstant` / `RelyOnNamed`, including const-if, sizes, fills, patterns and literal adaptation. | Restore site and explanation together. Do not clear an earlier live constant obligation. |
| `refwrite` | `NoteWritableRef` records the first writable binding, before or after a proof. | Restore the previous binding location. Actual calls and successful prior roots retain their evidence. |
| `extentuse`, `extentwhat`, `extentcap` | `RelyOnExtent` records the first global length/capacity dependency; `CheckVarExtent` and `NoteWritableRef` consume the group. | Restore all three together, including which extent was relied on. |
| `slotref` | Address taking, `AutoRef`, slot reads/stores and `ReplayEnvExits`. `ResetLocal` preserves it across passes. | Restore the old flag, not the OR of speculative and old evidence. |

The writer audit also includes the aggregate reset in `ResetLocal` and the
`Prov`/`Roots` mutators, not just direct `field = value` assignments. Optimizer
cloning/reassociation/tail-recursion writes occur after checking and are not
part of a `NeedsCaller` transaction.

## State behind the variable records

Restoring `VarDef::type` alone cannot undo mutations of a shared type detail.
Two behavioral probes establish the required treatment:

- A deferred `DATA.push("x")` must not choose the element type of a preexisting
  `var DATA=[]`; a later real exported `DATA.push(1)` infers its integer type.
- A generic struct/enum instance created only by a deferred helper must not
  retain a layout after its global size proofs are rolled back. A later real
  use followed by a writable reference must reestablish and reject that
  conflict. If no real use exists, the discarded layout must impose no proof.

The first-write `Writing(TypeArray*)` barrier therefore saves complete
preexisting `TypeArray` details (element,
evaluated size, size-expression pointer, kind and length-storage metadata).
Rollback removes every new struct/enum instance from declaration and AST
usable caches and retains ownership in quarantine. `Publishing` journals
instance links before `GetStructInst` / `GetEnumInst` populate them. It covers
**new and old details**: a newly resolved source signature can publish a new
detail which a future real call can reach. Those links return to their entry
values instead of scanning all AST types. A link to an older complete instance
may conservatively return to null too; lookup finds its still-valid declaration
cache again. Declaration cache removal visits only owners of new products and
trims their new suffixes, including completed recursive members. New variable and type records also leave the usable AST lists:
whole-AST consumers such as relative-root sizing enumerate those lists directly,
so merely removing function/type instances would still expose discarded types.
Existing complete instances are immutable after validation and
retain their prior proofs. Shared declaration-field arrays whose size was
evaluated speculatively are restored too. Derived stable-type, element and
type-pair query caches are cleared, so none can answer using rolled-back
inference or quarantined instances. `pendingpools` restores touched keys only.

## Other persistent checker state

| State | Treatment and reason |
|---|---|
| New function specs, including completed recursive members | Remove from every usable function cache; keep AST ownership in quarantine. No active-frame-only invalidation. |
| Existing complete function specs | Bodies stay read-only. Restore reused root/view metadata, `storesout` and added caller edges. Never rewrite an old stale body in a deferable transaction. |
| Store events | Record the entry length. `WritingStore` journals a first overwrite of an old entry in `ApplyCalleeStores`; truncate appended events and restore old entries on deferral. |
| `madestores` | Append-only (`AddStoreEvent`, `NoteGlobalBinding`); restore its entry length. |
| Class uses | `UsingClass` records whether a touched key existed and its vector length. `NoteClassUse` only appends; restore that length or erase the new key. |
| Threaded classes | `WritingThread` saves a touched old entry, or absence of a new key, before `NoteThreadedClass`, `ValidateThreadArgs`, `Unthread`, and initial bounded-class setup mutate it or its parent/heirs. |
| Pending pools | `WritingPending` saves the old non-null value or key absence before the declaration writes it. |
| Literal checks, resize/growth conflicts and delayed cast verdicts | Restore entry lengths so discarded checks impose no later judgments. |
| Named-result uses | Restore the entry prefix. Before the first erase of an old entry, `RemovingNamedResult` saves that prefix; append/new-entry erases alone need only an entry length. |
| Scope/frame/body/loop/type-build stacks and global flow | Existing checkpoint/RAII recovery restores entry state. |
| `ParamDefaultEnv`, `CheckDefaultInit`, function-value environments | Created for each execution-site check with `NewFunValEnv`; no reusable default-environment cache is published on the declaration. Their AST ownership remains valid, while cached call products are quarantined. Real uses clone/check defaults and captures again. |
| Type names, `indexarrays`, `poolglobals` | Declaration identity registries from `ResolveIndexTypes` / `ResolvePools`, not inferred variable evidence. Keep resolved identities and declaration restrictions; do not confuse them with `refwrite` or layout-size proofs. |
| `declsiteof`, `namedoutside`, node-value/shape maps | Entries are keyed by distinct owned specialization/node pointers. Quarantined bodies cannot be found through usable function/type caches; a fresh body gets fresh keys. |
| AST nodes/functions, `fvenvs`, shader/embed storage | Ownership/source resources remain allocated. No live call graph is published by the discarded root; retained allocation prevents dangling pointers. New variables/types have separate quarantine ownership and leave the usable lists. |
| Previously reported errors and successful roots | Keep them. Deferral is not a diagnosed failure, and never clears another root's diagnostic or proof. |

`test/const_if_marks.py` checks the original reference/constant/nonnegative
failures, completed generic/nested/recursive callees, const-for/constructor
fragments, actual writes, defaults, earlier live marks and their original
locations, shared pending inference, discarded/live generic layout proofs in
both declaration orders, O0/O2 checking and library emission, native C hosts,
JSON diagnostics and editor valid/error/repaired transitions.


## Mutation barriers and the exhaustive oracle

Initialization of a newly allocated record needs no undo. Rechecking an existing
local goes through `ResetLocal` before any declaration/parameter/binder setup.
A stale preexisting specialization is not rechecked in a deferable root. Its
completed body, parameters, and synthetic class roots remain read-only.

The other writers that can reach preexisting variables use these barriers:

- `LookupVar`: capture discovery.
- `NoteWritableRef`, `RelyOnNonneg`, `RelyOnConstant`, `RelyOnExtent`,
  `ResizesToMark`: persistent obligations and original use locations.
- `AutoRef` / address-taking: slice-slot reference evidence.
- `BindProv`, `BindRefProvenance`, `AddBinding`, `CheckRefRebindRoot`:
  complete provenance and binding updates, including `Roots` mutators.
- `AddContents`, `RecordStore`, `ApplyCalleeStores`, `NoteSlotStore`:
  holder alternatives, mapped reference stores, and byte-view evidence.
- `RestoreFlow`, `NarrowCond`, `KillNarrow`, assignment/rebinding,
  `ReplayEnvExits`, and function exit replay: assigned/narrowed flow.
  Restoring an already-equal global narrowing does no write and makes no undo
  copy. The ordinary root checkpoint still restores global flow on errors.
- `ArraySize` and `CompletePending`: evaluated extents and inferred elements.
  Other array-detail writes initialize newly allocated details before publication.

`GOOSE_DEFERRED_VERIFY=1` enables an exhaustive testing oracle. It snapshots all
entry records and auxiliary collections, then checks that sparse undo would
reconstruct that exact state on success, diagnosed failure, and deferral. It
compares an undo value with the root-entry value, so a barrier placed *after*
the first mutation fails too. After rollback it compares restored objects,
never moved-from undo entries. It also captures new variable/array annotations
immediately before deferral and checks that quarantine preserves them. Instance
links have the separate revocation rule above. Floating analysis facts compare
representation bits (including NaN payloads and signed zero) before defaulted
member equality; NaNs are normalized for that second comparison. Defaulted
`VarDef` equality keeps future members in the oracle.

This opt-in oracle deliberately has the old exhaustive cost. It must be absent
from measurements. It changes no language semantics and is off by default.

## Work bounds and remaining costs

With the oracle disabled, root entry stores lengths and allocation boundaries;
it does not copy unrelated variables, array details, stores, or maps. Variable
and array undo cost is proportional to the complete records first written in
that root, including their vector payloads. Auxiliary undo visits touched keys,
overwritten old store entries, and reused specialization metadata. Rollback
also visits the root's new products and published instance links. No whole-
program return-from scan or guessed call graph is used to elide checking:
indirect calls, function values, defaults, formatting, overloads, and selected
branches all follow the same transaction rules.

This does **not** claim that the entire compiler is linear. The inherited
root/global-flow checkpoint still scans G globals per root (O(U*G), and global
initialization has O(G²) such work). Existing name/candidate lookup, flow and
provenance analyses retain their own costs. Repeatedly mutating a single large
old variable or threaded-class record still copies that record's complete
payload once per root. Erasing an old pending named-result entry copies the
old named-result prefix once. Quarantined allocations and allocation-identity
maps consume memory proportional to owned objects until the AST is destroyed;
this change introduces no reclamation or runtime behavior.

`test/deferred_state_work.py` uses `GOOSE_DEFERRED_WORK=1` JSON counters for
copied variable/array records, auxiliary undo records, and transaction-wide
AST type visits. It checks 0/24/48/96 functions, ordinary computations, generic
calls, arrays, slice stores, successful/deferred roots, unrelated named returns,
std imports, growing unrelated globals, prior live proofs, real calls, and the
floating oracle cases. It runs the exhaustive oracle separately. Bounds concern
structural work, never wall-clock thresholds. The full runner registers it and
`test/compiler_check_harness.py`; the existing 825 checks retain behavior,
layout/cache/proof, CLI/JSON and editor coverage.

The measurement harness prints a read-only plan without launching a compiler:

```sh
python3 bench/shared_native/compiler_check.py --globals 500 --sizes 250 500 1000 \
  --case ordinary --case calls --case stores --case deferred-stores \
  --stdlib --named-return
```

It also accepts repeated `--source` paths for real projects, and configurable
samples/warmups. Only explicitly coordinated `--run` launches timing processes;
it requires baseline/extended binaries and an output path. Each source has a
hash; compiler identities/hashes are checked before and after measurements.
No timing result is claimed by the deterministic acceptance tests.

The coordinated [measurement record](../../bench/shared_native/results/deferred-state-2026-10-23/README.md)
compares frozen pre-fix `8464cc68` and corrected `41dc6eb3` Release compilers.
It includes ordinary computations through 4,000 unused functions, std imports,
generic calls, stored slices, deferred roots, an upstream control and the real
`parallel_wasm` source. Raw wall/RSS samples and provenance remain separate
from the structural acceptance tests; these measurements do not establish
whole-compiler linearity.
