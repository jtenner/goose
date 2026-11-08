// The right operand must not change the captured left value.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';
import { snapshotMemory } from './wasm_memory_snapshot.mjs';
const image = Buffer.alloc(16); image.writeBigInt64LE(7n); image.writeBigInt64LE(8n, 8);
const labels = ['before', 'right-live', 'after'];
let runtime, initial, expected, source, visits = 0;
runtime = instantiate(fs.readFileSync(process.argv[2]), bytes => {
    const label = Buffer.from(bytes).toString('utf8').trim();
    assert.equal(label, labels[visits++]);
    assert.equal(runtime.instance.exports.test_stack_top_0.value,
        initial + (label === 'right-live' ? 32 : 0), 'temporary equality live frame top differs');
    const memory = runtime.instance.exports.memory;
    if (label === 'before') {
        const before = snapshotMemory(memory);
        source = before.subarray(0, initial).indexOf(image);
        assert(source >= 0);
        assert.equal(before.subarray(0, initial).indexOf(image, source + 1), -1);
        new Uint8Array(memory.buffer).fill(0xa5, initial, initial + 65);
        new Uint8Array(memory.buffer)[initial + 64] = 0x5a;
        expected = snapshotMemory(memory);
        image.copy(expected, initial);
        expected.writeBigInt64LE(9n, source);
    } else {
        if (label === 'after') image.copy(expected, initial + 16);
        assert.deepEqual(snapshotMemory(memory), expected, 'temporary equality captured image differs');
    }
    assert.equal(runtime.pendingPrints, 0);
    fs.writeSync(1, bytes);
});
initial = runtime.instance.exports.test_stack_top_0.value;
runCompleted(runtime);
assert.equal(visits, 3);
assert.equal(runtime.instance.exports.test_stack_top_0.value, initial,
    'temporary equality completed frame top differs');
assert.deepEqual(snapshotMemory(runtime.instance.exports.memory), expected,
    'temporary equality completed image differs');
