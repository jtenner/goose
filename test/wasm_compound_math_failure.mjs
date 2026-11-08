import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate, GooseFailure } from '../scripts/run_wasm.mjs';
import { snapshotMemory } from './wasm_memory_snapshot.mjs';
const [file, kind] = process.argv.slice(2);
const second = kind === 'overflow' ? -9223372036854775808n : 9n;
const pattern = Buffer.alloc(16); pattern.writeBigInt64LE(8n); pattern.writeBigInt64LE(second, 8);
let runtime, expected, permanent;
runtime = instantiate(fs.readFileSync(file), bytes => {
    assert.equal(Buffer.from(bytes).toString('utf8'), 'before\n');
    permanent = runtime.instance.exports.test_stack_top_0.value;
    expected = snapshotMemory(runtime.instance.exports.memory).subarray(0, permanent);
    const target = expected.indexOf(pattern); assert(target >= 0);
    assert.equal(expected.indexOf(pattern, target + 1), -1);
    expected.writeBigInt64LE(kind === 'modulo' ? 2n : 4n, target);
    fs.writeSync(1, bytes);
});
const reason = kind === 'overflow' ? /integer division overflow/ : /division by zero/;
assert.throws(() => runtime.run(), error => error instanceof GooseFailure && reason.test(error.message));
assert(expected, 'compound failure checkpoint did not run');
assert.deepEqual(snapshotMemory(runtime.instance.exports.memory).subarray(0, permanent), expected,
    'compound partial-write memory image differs');
assert.equal(runtime.pendingPrints, 0); assert.equal(runtime.pendingSnapshots, 0);
