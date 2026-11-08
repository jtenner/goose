import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';
import { snapshotMemory } from './wasm_memory_snapshot.mjs';
let runtime, initial, frame, data, visits = 0;
runtime = instantiate(fs.readFileSync(process.argv[2]), bytes => {
    const label = Buffer.from(bytes).toString('utf8').trim();
    assert.equal(runtime.instance.exports.test_stack_top_0.value, initial + 16,
        'limited data conversion live frame top differs');
    assert.equal(runtime.instance.exports.test_stack_top_1.value, label === 'before' ? 1 : 2058,
        'limited data conversion live data top differs');
    if (label === 'before') {
        assert.equal(visits++, 0);
        new Uint8Array(runtime.memory.buffer)[initial + 16] = 0x6c;
        frame = snapshotMemory(runtime.memory);
        assert.equal(frame.readBigInt64LE(initial), 7n);
        assert.equal(frame.readBigInt64LE(initial + 8), -8n);
        const view = new Uint8Array(runtime.instance.exports.data_memory_1.buffer);
        view.fill(0x5a, 1); view[2058] = 0xc5;
        data = snapshotMemory(runtime.instance.exports.data_memory_1);
        data.writeUInt32LE(1, 1); data[5] = 7; data.writeUInt16LE(2, 6);
        data.writeBigInt64LE(7n, 8); data.writeBigInt64LE(-8n, 16);
        data.writeUInt16LE(65000, 2056);
    } else {
        assert.equal(label, 'after'); assert.equal(visits++, 1);
        assert.deepEqual(snapshotMemory(runtime.memory), frame, 'limited data conversion memory 0 image differs');
        assert.deepEqual(snapshotMemory(runtime.instance.exports.data_memory_1), data,
            'limited data conversion data image differs');
    }
    assert.equal(runtime.pendingPrints, 0); fs.writeSync(1, bytes);
});
initial = runtime.instance.exports.test_stack_top_0.value;
runCompleted(runtime); assert.equal(visits, 2);
assert.equal(runtime.instance.exports.test_stack_top_0.value, initial);
assert.equal(runtime.instance.exports.test_stack_top_1.value, 1);
assert.deepEqual(snapshotMemory(runtime.memory), frame);
assert.deepEqual(snapshotMemory(runtime.instance.exports.data_memory_1), data);
