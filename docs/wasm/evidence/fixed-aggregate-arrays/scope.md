# First Memory 0 fixed aggregate-array increment

Parent 0d64e43d32f17485526beef0d463e9c9abad9102. Eight fixture candidates pass native O0/O2 on preserved compiler25090248 and all reach the prior aggregate-element target guard. No timing has been acquired.

Admit positive-stride fixed struct/enum/selected-variant elements only in fixed/static-capacity limited arrays in Memory0. Reuse checked numeric layouts and fresh child ranges. Support explicit literals, exact fresh copies, indexed fields/reference calls/matches, length/capacity/clear, and by-reference iteration through existing admitted paths. Finish one element before evaluating the next; limited literals publish their checked count first, matching the native source. Owned-name copies use direct0-to0 memory.copy without per-element scratch locals.

Keep aggregate fills/defaults, push/pop, by-value iteration, whole replacement/equality/printing, adapted arrays, direct nested array elements, zero-stride variants and data-memory aggregate elements guarded. No reference ABI widening; all admitted inline array headers/payloads stay in Memory0. Field-path iteration remains guarded; a named array reference can use the existing loop path.

Next checks: frozen Release and targeted Node/Wasmtime; native-valid operation gates and data-resident embedded-inline-array negative; constructor length/effect order/global observation; named/literal32/256 local scaling; sparse65536capacity footprint; bounds/control failures; completed owners; old744suite/native/exact comparisons; independent review. Measure compiler/runtime/physical-memory costs in a later fresh coordinated scope before full backend acceptance.
