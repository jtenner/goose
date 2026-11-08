# Fixed source to static-limited whole-array assignment

Five native-valid saved parent cases reject at the current Wasm whole-array
assignment adaptation guard. Inputs, generated C, native results, Wasm errors
and all subprocess statuses are preserved in parent01. The parent compiler is
the current fixed-array-layout candidate; record its commit after that stage
passes and is committed. No source change for this stage has been made yet.

The generated native main for stored.c uses gs_memmove(c_g.e,a_g.e,2*8), then
sets c_g.len. It does not overwrite the unused third element. The target path
must preserve that rule; copying the entire capacity-sized temporary is wrong.

Narrow plan:
- Reuse CanCopyFixedArray only for A_FIXED -> A_LIMITED, matching elements and
  source count within capacity. Keep all other old assignment guards.
- The caller already captures the destination address before RHS evaluation.
  Use WithReadPlace for the source, with its existing intrinsic call temporary
  and reference null checks. Copy bytes before writing the count.
- Add the checked limited prefix to the captured payload address. Keep memory
  identity and carry/span checks through the existing CopyBytes service.
- memory.copy has memmove overlap semantics. Pure stored values need no added
  temporary. Calls and true temporaries retain the existing read-place lifetime.
- Write only the active payload and count, with no unused-capacity store.
- Cover Memory 0/data destinations and sources, selected LHS/RHS order, references,
  callbacks, zero sources/effects, wide prefixes, aliasing and posttrap recovery.
- Full observers must compare the retained unused capacity and outside sentinels;
  valid oversized-copy and wrong-prefix mutants must fail their named assertions.

Correctness only. No timing, measurement leases, or performance gate.
