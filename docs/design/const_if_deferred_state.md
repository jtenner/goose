# Deferred standalone analysis state

This audit covers the `NeedsCaller` rollback in `TypeCheck::Checkpoint`.
It is separate from recovery after a diagnosed error. A deferred helper has
no surviving call path, so it cannot leave new writable-reference evidence or
proof obligations on globals. Earlier real roots' obligations must survive,
including their original source locations.

`EnvRead` is a call-replay/flow record, not a complete variable snapshot.
`DeferredState` therefore copies every preexisting `VarDef` by value and restores
it into the **same object** on deferral. All 51 current members are accounted
for below. New variables remain owned by the AST with the quarantined checks;
they never replace preexisting objects. A successful root commits normally.

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

Rollback therefore restores complete preexisting `TypeArray` details (element,
evaluated size, size-expression pointer, kind and length-storage metadata).
It removes every new struct/enum instance from declaration and AST usable
caches, clears type-expression links to those instances, and retains ownership
in quarantine. New variable and type records also leave the usable AST lists:
whole-AST consumers such as relative-root sizing enumerate those lists directly,
so merely removing function/type instances would still expose discarded types.
Existing complete instances are immutable after validation and
retain their prior proofs. Shared declaration-field arrays whose size was
evaluated speculatively are restored too. Derived stable-type, element and
type-pair query caches are cleared, so none can answer using rolled-back
inference or quarantined instances. `pendingpools` is restored.

## Other persistent checker state

| State | Treatment and reason |
|---|---|
| New function specs, including completed recursive members | Remove from every usable function cache; keep AST ownership in quarantine. No active-frame-only invalidation. |
| Existing complete function specs | Bodies stay read-only. Restore reused root/view metadata, `storesout` and added caller edges. Never rewrite an old stale body in a deferable transaction. |
| Store events, mapped stores, class uses and threaded classes | Restore the existing whole-root snapshots; these include mutations to old entries, not just appended items. |
| Literal checks, named-result uses, resize/growth conflicts and delayed cast verdicts | Restore the existing transaction snapshots/prefixes so discarded checks impose no later judgments. |
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
