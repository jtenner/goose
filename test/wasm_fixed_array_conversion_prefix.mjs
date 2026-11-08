import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';
import { snapshotMemory } from './wasm_memory_snapshot.mjs';
const count = Number(process.argv[3]), frame = 2 * Math.max(1, count), temp = Math.max(1, count);
const prefix = []; let value = count;
do { const byte = value % 128; value = Math.floor(value / 128); prefix.push(byte | (value ? 128 : 0)); } while (value);
const end = 1 + prefix.length + count;
let runtime, initial, expected, dataExpected, visits = 0;
runtime = instantiate(fs.readFileSync(process.argv[2]), bytes => {
    const label = Buffer.from(bytes).toString('utf8').trim();
    const memory = runtime.instance.exports.memory, data = runtime.instance.exports.data_memory_1;
    assert.equal(runtime.instance.exports.test_stack_top_0.value, initial + frame,
        'fixed array prefix live frame top differs');
    if (visits++ === 0) {
        assert.equal(label, 'before'); assert.equal(runtime.instance.exports.test_stack_top_1.value, 1);
        new Uint8Array(memory.buffer).fill(0xa5, initial + frame, initial + frame + temp);
        new Uint8Array(memory.buffer)[initial + frame + temp] = 0x6c;
        expected = snapshotMemory(memory); expected.fill(3, initial + frame, initial + frame + count);
        new Uint8Array(data.buffer).fill(0x5a, 1); new Uint8Array(data.buffer)[end] = 0xc5;
        dataExpected = snapshotMemory(data); dataExpected.set(prefix, 1);
        dataExpected.fill(3, 1 + prefix.length, end);
    } else {
        assert.equal(label, 'after');
        assert.equal(runtime.instance.exports.test_stack_top_1.value, end,
            'fixed array prefix live data top differs');
        const actual = snapshotMemory(memory);
        if (!count) expected[initial + frame] = actual[initial + frame]; // Owned identity, no payload.
        assert.deepEqual(actual, expected, 'fixed array prefix memory 0 image differs');
        assert.deepEqual(snapshotMemory(data), dataExpected, 'fixed array prefix data image differs');
    }
    assert.equal(runtime.pendingPrints, 0); fs.writeSync(1, bytes);
});
initial = runtime.instance.exports.test_stack_top_0.value;
runCompleted(runtime); assert.equal(visits, 2);
assert.equal(runtime.instance.exports.test_stack_top_0.value, initial);
assert.equal(runtime.instance.exports.test_stack_top_1.value, 1);
assert.deepEqual(snapshotMemory(runtime.instance.exports.memory), expected);
assert.deepEqual(snapshotMemory(runtime.instance.exports.data_memory_1), dataExpected);
