# Fixed constructor assignment

Exact fixed structs, enums and variants can be replaced by a plain constructor,
empty enum constant or checked fixed default. The target is captured first.
The new value is then constructed in a separate checked Memory 0 reservation.
Only the complete value is copied to the target. Initializers and field defaults
therefore still see the old target. References keep their actual source addresses.

The temporary has a compiler-only owner record. It does not invent a frontend
variable or use the data-memory top dispatcher for Memory 0. The checked frame
reserve helper returns its base and installs one ordered cleanup action before
any initializer runs. Normal completion copies before cleanup. Return, break
and continue use the same cleanup list. Inner defers run while the temporary is
live; outer defers run after its release. Empty images reserve one byte for the
owner, while their stored copy remains zero bytes.

Native-first checks prove the prior constructor rejection on valid programs.
The cases include defaults reading the old target, shallow references into that
target, nested fields, limited arrays, empty variants, global initialization,
frame growth, dynamic memory targets and left-before-right evaluation. Early
returns and loop exits must leave the target unchanged. A runtime division
failure is observed against a copied complete permanent Memory 0 prefix.
The unfinished constructor does not change that image.

A focused read-only review found no confirmed owner or cleanup defect, but
identified missing array-element exit coverage. Native-first tests then proved
that always-exiting scalar and aggregate array elements still failed Wasm
compilation. Fixed construction now emits these exits without trying to convert
or copy a nonexistent value. Fixed and limited arrays, fresh data elements,
named element copies and nested constructor assignments have separate checks.
The review is for the earlier source snapshot; its report and the later failing
and passing records are kept separate.

Inactive enum bytes remain unspecified. These tests do not require identical
constructor padding from native code and Wasm. Whole-image assignment checks
for existing values remain in the earlier fixed-assignment suite. The complete
Memory 0/data matrix also remains enabled in correctness-only mode.

The final correctness-only suite passes 1,656 groups, including all forty
complete Memory 0/data matrix cases. The native baseline passes 1,870 frontend
groups, 911 generated-C runs, 1,083 TinyCC runs and all other baseline groups.
All 52 exact comparisons pass; 314 unchanged-source parent modules are
byte-identical. The final compiler SHA256 is
`87903c01842fabdfcb8900cdd1536b6f4995811b41106634da4e6529b49d5f06`.
Source, test and compiler hashes match before and after the final runs.
The focused record has 44 native-reused/both-engine cases, 28 live-owner/control
groups, two failed-value image groups and two invalid-target groups.

Raw records are retained in
`/tmp/goose-wasm-constructor-assignment-20261107`. Failed intermediate compilers,
invalid zero-size field fixtures, harness errors and all successful outputs
remain in separate directories. The final compiler and validation records are
listed in the [archived manifest](constructor-assignment/archive-manifest.json).

This work uses correctness checks only. It has no measurement acceptance gate,
precision timing, physical-memory claim or measurement-lease rotation. General
aggregate-valued calls and results, array fills/defaults, whole-array assignment,
relative and nonfixed layouts remain separate compilation work.
