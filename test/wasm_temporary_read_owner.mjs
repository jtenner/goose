// Observe the temporary and the effectful index frame while both owners are live.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';
import { snapshotMemory } from './wasm_memory_snapshot.mjs';
const labels = ['before', 'index-live', 'after'];
let runtime, initial, expected, visits = 0;
runtime = instantiate(fs.readFileSync(process.argv[2]), bytes => {
    const label = Buffer.from(bytes).toString('utf8').trim();
    assert.equal(label, labels[visits++]);
    assert.equal(runtime.instance.exports.test_stack_top_0.value,
        initial + (label === 'index-live' ? 32 : 0), 'temporary read live frame top differs');
    const memory = runtime.instance.exports.memory;
    if (label === 'before') {
        new Uint8Array(memory.buffer)[initial + 32] = 0x5a;
        expected = snapshotMemory(memory);
        expected.writeBigInt64LE(7n, initial);
        expected.writeBigInt64LE(8n, initial + 8);
        expected.writeBigInt64LE(99n, initial + 16);
        expected.writeBigInt64LE(100n, initial + 24);
    } else {
        if (label === 'after') expected.writeBigInt64LE(1n, initial + 16);
        assert.deepEqual(snapshotMemory(memory), expected, 'temporary read live image differs');
    }
    assert.equal(runtime.pendingPrints, 0);
    fs.writeSync(1, bytes);
});
initial = runtime.instance.exports.test_stack_top_0.value;
runCompleted(runtime);
assert.equal(visits, 3);
assert.equal(runtime.instance.exports.test_stack_top_0.value, initial,
    'temporary read completed frame top differs');
assert.deepEqual(snapshotMemory(runtime.instance.exports.memory), expected,
    'temporary read completed image differs');
