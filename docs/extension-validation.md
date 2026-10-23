# Native compiler extension validation

Baseline: upstream `94cc64daeabcae6f072dc1fe2b864acda5a001bc`, fork
`jtenner/goose`, Linux x86_64, AMD Ryzen 7 8845HS (16 logical CPUs), GCC
14.2.0, Clang 23.1.3, CMake 4.4.4, Python 3.13. Upstream runtime version:
`a5dbd11b6309`. Optional audio/gfx/physics/ui packages were not built in.

Commands:

```sh
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release -j 6
PATH=/home/dev/.local/share/mise/installs/clang/23.1.3/bin:$PATH \
  python3 test/run_tests.py --profile baseline --cc native --require-clang -j 6
```

The clean upstream build succeeded: configuration 0.409 seconds, build 77.907
seconds, peak compiler-build child RSS 2,202,504 KiB. The full baseline suite
passed in 142 seconds, including 51 sample checks, native C at O0/O2, TinyCC
runs, compiler/runtime unit tests, diagnostics, documentation examples,
language-server checks, and the Goose-in-Goose bootstrap. Threaded TinyCC
programs and optional multimedia execution were skipped as documented upstream.
The compiler emitted existing GCC warnings; no compiler errors occurred.

The initial run had eight environment failures: the installed `clang` shim
had no selected version. Prepending the actual installed compiler directory
resolved them without repository changes. The passing run used a separate
clean upstream worktree to keep source-inspection checks independent of edits.

Native definitions acceptance tests were committed before implementation;
the unmodified compiler rejected the first invocation with `unknown option:
--define`. Run the focused tests with
`python3 test/cli_definitions.py build/goose`.
