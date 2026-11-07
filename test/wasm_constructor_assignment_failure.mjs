import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate, GooseFailure } from '../scripts/run_wasm.mjs';
import { snapshotMemory } from './wasm_memory_snapshot.mjs';
const [file, kind] = process.argv.slice(2);
let runtime, saved, permanent;
runtime = instantiate(fs.readFileSync(file), bytes => {
    assert.equal(Buffer.from(bytes).toString('utf8'), 'before\n');
    permanent = runtime.instance.exports.test_stack_top_0.value;
    saved = snapshotMemory(runtime.instance.exports.memory).subarray(0, permanent);
    fs.writeSync(1, bytes);
});
const failure = kind === 'bounds' ? /array index out of bounds/ : /division by zero/;
assert.throws(() => runtime.run(), error => error instanceof GooseFailure && failure.test(error.message));
if (kind === 'bounds') assert.equal(runtime.instance.exports.test_stack_top_0.value, permanent,
    'invalid target started a constructor temporary');
assert(saved, 'constructor failure checkpoint did not run');
assert.deepEqual(snapshotMemory(runtime.instance.exports.memory).subarray(0, permanent), saved,
    'failed constructor changed the permanent Memory 0 image');
assert.equal(runtime.pendingPrints, 0);
assert.equal(runtime.pendingSnapshots, 0);
