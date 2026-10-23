# Native configuration operands in shared memory APIs

This nested fixture requires explicit native definitions and is run by:

```sh
python3 test/native_config_definitions.py /path/to/integrated/goose
```

It uses CLI string definitions directly and through immutable global aliases
(two alias levels) for atomic load/store/CAS success and failure orders and
page advice. Both selected const-if branches are checked/executed. Two valid
order/advice profiles, both endian booleans, both alias modes, Goose O0/O2
and C O0/O2 give 32 native configurations. Twelve additional native builds
verify that inactive invalid/non-string/undefined order operands are ignored.
There are 54 rejection checks for selected illegal orders, invalid CAS failure
strength/order, unknown advice, non-string/undefined definitions, and wrong
integer/bool operands. These counts describe the full successful matrix;
a compiler without native-definition string extraction fails the regression.

Generated C must use the selected atomic order constants and page-advice
ordinal. Native execution checks stores, successful and failed CAS for both
atomic widths, actual readonly-map advice calls, and unaligned bounded scalar
reads/writes using direct integer/bool definitions and their global aliases.
Definitions are typed: the i64 CLI payload is explicitly cast to u16 before
writing; no implicit narrowing or C preprocessor macro is involved. First-byte
checks independently verify both byte orders. All program logic is Goose.

The normal Linux native baseline registers this script with the Wasm64 smoke,
clobber, conditional-layout alignment matrix and read-only benchmark-plan
checks. The default full 3000-job Wasm stress remains an explicit command.
The baseline registration does not depend on TinyCC being available, and never
executes the benchmark workload harness. Other OS/profile/backend combinations
skip these Linux native execution suites.
