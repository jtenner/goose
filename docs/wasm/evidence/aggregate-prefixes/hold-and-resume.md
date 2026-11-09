# Owner hold and correctness resume

The second full Wasm run was stopped with SIGTERM at the owner's profiling
quiet-hold request. Its wrapper exit -15 and partial artifacts are preserved.
The final owned-process check found wrapper, test and current Wasmtime child
all absent. No command ran during the hold.

After explicit owner release, source85/test5825/compiler hashes still matched.
Only the full Wasm suite restarted, in full-correctness03 at lower scheduling
priority. Native, exact, assertion-enabled and focused checks were not repeated.
No measurement, profiling or lease operation was performed by this thread.
