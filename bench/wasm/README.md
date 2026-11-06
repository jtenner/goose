# Initial scalar Wasm measurements

These workloads establish a first baseline. They do not compare an optimization
with a previous Wasm backend. `scalar.goose` uses only core integer operations.
`conversion.goose` exposes the initial host-call/BigInt cost of wrapping float
conversion. There is no added guest heap allocation in the integer loop.

Run `measure.py` only in a coordinator-approved quiet window after all owned
builds and tests finish. Its required lease JSON records `active: true` and
`owner: "/root"`. Use explicit versions of Node and wasm-tools on PATH.

The harness saves every sample, two warmups, seven measured runs, source and
binary identities, module size, addressable Memory 0 size, process peak RSS,
Goose invocation time, and engine identity. Node's run samples exclude
compilation/instantiation but include one scalar print to a captured sink.
Compilation/initialization samples include the JS adapter and may use V8's
module cache. Native samples include process startup and exit. Do not divide
these timings to claim a native/Wasm speed ratio. No virtual-reservation or
physical linear-memory commitment measurement is provided.

Multi-memory dispatch, aggregate construction, nonlocal EH, and worker benchmarks
remain part of stages C through G. No speed claim is made for those features.
