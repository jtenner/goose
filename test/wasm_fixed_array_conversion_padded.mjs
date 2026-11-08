import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';
import { snapshotMemory } from './wasm_memory_snapshot.mjs';
let runtime, initial, expected, dataExpected, visits = 0;
runtime = instantiate(fs.readFileSync(process.argv[2]), bytes => {
    const label = Buffer.from(bytes).toString('utf8').trim();
    const memory = runtime.instance.exports.memory, data = runtime.instance.exports.data_memory_1;
    assert.equal(runtime.instance.exports.test_stack_top_0.value, initial + 56,
        'fixed array padded live frame top differs');
    if (visits++ === 0) {
        assert.equal(label, 'before'); assert.equal(runtime.instance.exports.test_stack_top_1.value, 1);
        for (const [i, offset] of [4, 18, 32, 46].entries())
            new Uint8Array(memory.buffer).set([0xc1 + i, 0xd1 + i], initial + offset);
        new Uint8Array(memory.buffer).fill(0xa5, initial + 56, initial + 84);
        new Uint8Array(memory.buffer)[initial + 84] = 0x6c;
        expected = snapshotMemory(memory);
        expected.writeFloatLE(-1.25, initial + 56); expected.writeDoubleLE(7.875, initial + 62);
        expected.writeFloatLE(5.0, initial + 70); expected.writeDoubleLE(1.25, initial + 76);
        new Uint8Array(data.buffer).fill(0x5a, 1); new Uint8Array(data.buffer)[33] = 0xc5;
        dataExpected = snapshotMemory(data); dataExpected.writeUInt32LE(2, 1);
        expected.copy(dataExpected, 5, initial + 56, initial + 84);
    } else {
        assert.equal(label, 'after');
        assert.equal(runtime.instance.exports.test_stack_top_1.value, 33,
            'fixed array padded live data top differs');
        assert.deepEqual(snapshotMemory(memory), expected, 'fixed array padded memory 0 image differs');
        assert.deepEqual(snapshotMemory(data), dataExpected, 'fixed array padded data image differs');
    }
    assert.equal(runtime.pendingPrints, 0); fs.writeSync(1, bytes);
});
initial = runtime.instance.exports.test_stack_top_0.value;
runCompleted(runtime); assert.equal(visits, 2);
assert.equal(runtime.instance.exports.test_stack_top_0.value, initial);
assert.equal(runtime.instance.exports.test_stack_top_1.value, 1);
assert.deepEqual(snapshotMemory(runtime.instance.exports.memory), expected);
assert.deepEqual(snapshotMemory(runtime.instance.exports.data_memory_1), dataExpected);
