import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';
import { snapshotMemory } from './wasm_memory_snapshot.mjs';
let runtime, initial, frame, data, visits = 0;
runtime = instantiate(fs.readFileSync(process.argv[2]), bytes => {
    const label = Buffer.from(bytes).toString('utf8').trim();
    assert.equal(runtime.instance.exports.test_stack_top_0.value, initial + 16,
        'data array assignment live frame top differs');
    assert.equal(runtime.instance.exports.test_stack_top_1.value, 2058,
        'data array assignment live data top differs');
    if (label === 'before') {
        assert.equal(visits++, 0);
        new Uint8Array(runtime.instance.exports.memory.buffer)[initial + 16] = 0x6c;
        new Uint8Array(runtime.instance.exports.data_memory_1.buffer)[2058] = 0xc5;
        frame = snapshotMemory(runtime.instance.exports.memory);
        assert.deepEqual([0, 8].map(n => frame.readBigInt64LE(initial + n)), [7n, -8n]);
        data = snapshotMemory(runtime.instance.exports.data_memory_1);
        assert.equal(data.readUInt32LE(1), 1); assert.equal(data[5], 7);
        assert.equal(data.readUInt16LE(6), 3); assert.equal(data.readUInt16LE(2056), 65000);
        assert.deepEqual([8, 16, 24].map(n => data.readBigInt64LE(n)), [1n, 2n, 3n]);
        data.writeUInt16LE(2, 6); data.writeBigInt64LE(7n, 8); data.writeBigInt64LE(-8n, 16);
    } else {
        assert.equal(label, 'after'); assert.equal(visits++, 1);
        assert.deepEqual(snapshotMemory(runtime.instance.exports.memory), frame, 'data array assignment memory 0 image differs');
        assert.deepEqual(snapshotMemory(runtime.instance.exports.data_memory_1), data, 'data array assignment data image differs');
    }
    assert.equal(runtime.pendingPrints, 0); fs.writeSync(1, bytes);
});
initial = runtime.instance.exports.test_stack_top_0.value;
runCompleted(runtime); assert.equal(visits, 2);
assert.equal(runtime.instance.exports.test_stack_top_0.value, initial);
assert.equal(runtime.instance.exports.test_stack_top_1.value, 1);
assert.deepEqual(snapshotMemory(runtime.instance.exports.memory), frame);
assert.deepEqual(snapshotMemory(runtime.instance.exports.data_memory_1), data);
