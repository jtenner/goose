# Temporary fixed-array value equality

Correctness only. No timing, performance gate or measurement lease.

Native-first five families at O0/O2 passed using temporary-read build04. The mutation case prints true then9: left fixed-array value is captured before right change() mutates its source. Current Wasm compiler rejects effectful right operands and temporary left operands. Original records preserved.

Next design: only extend admitted fixed/limited scalar-reference element array comparisons. Snapshot the full left fixed image before right evaluation when either side is temporary or the right path has statements. Keep both owners live during comparison, capture boolean before cleanup. Use right scoped read and existing element/type/layout helpers. Keep stable non-effectful comparisons byte-identical. Nonfixed source snapshot/adaptation and nominal-element equality stay guarded. Tests must cover evaluation order, aliases, optional refs, FP, lengths, early exits, globals and complete live images/valid wrong-snapshot controls.

Do not edit source until temporary-read full validation and checkpoint are complete.
