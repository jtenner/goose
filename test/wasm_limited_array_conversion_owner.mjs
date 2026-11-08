import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';
import { snapshotMemory } from './wasm_memory_snapshot.mjs';
const mode = process.argv[3]; assert(['padded', 'varint'].includes(mode));
const frame = mode === 'padded' ? 43 : 258;
const end = mode === 'padded' ? 33 : 131;
let runtime, initial, expected, data, visits = 0;
runtime = instantiate(fs.readFileSync(process.argv[2]), bytes => {
    const label = Buffer.from(bytes).toString('utf8').trim(), e = runtime.instance.exports;
    assert.equal(e.test_stack_top_0.value, initial + frame, 'limited receiver live frame top differs');
    assert.equal(e.test_stack_top_1.value, label === 'before' ? 1 : end, 'limited receiver live data top differs');
    if (label === 'before') {
        assert.equal(visits++, 0);
        const view = new Uint8Array(e.memory.buffer);
        if (mode === 'padded') {
            view.set([0xc1, 0xd1], initial + 5); view.set([0xc2, 0xd2], initial + 19);
            view.fill(0xb6, initial + 29, initial + 43);
        } else {
            assert.equal(new DataView(e.memory.buffer).getUint16(initial, true), 128);
            assert.deepEqual([...view.subarray(initial + 2, initial + 130)], Array.from({length: 128}, (_, i) => i));
            view.fill(0xb6, initial + 130, initial + 258);
        }
        view[initial + frame] = 0x6c;
        expected = snapshotMemory(e.memory);
        const target = new Uint8Array(e.data_memory_1.buffer); target.fill(0x5a, 1); target[end] = 0xc5;
        data = snapshotMemory(e.data_memory_1);
        if (mode === 'padded') { data.writeUInt32LE(2, 1); expected.copy(data, 5, initial + 1, initial + 29); }
        else { data[1] = 0x80; data[2] = 1; expected.copy(data, 3, initial + 2, initial + 130); }
    } else {
        assert.equal(label, 'after'); assert.equal(visits++, 1);
        assert.deepEqual(snapshotMemory(e.memory), expected, 'limited receiver memory 0 image differs');
        assert.deepEqual(snapshotMemory(e.data_memory_1), data, 'limited receiver data image differs');
    }
    assert.equal(runtime.pendingPrints, 0); fs.writeSync(1, bytes);
});
initial = runtime.instance.exports.test_stack_top_0.value;
runCompleted(runtime); assert.equal(visits, 2);
const e = runtime.instance.exports;
assert.equal(e.test_stack_top_0.value, initial, 'limited receiver completed frame top differs');
assert.equal(e.test_stack_top_1.value, 1, 'limited receiver completed data top differs');
assert.deepEqual(snapshotMemory(e.memory), expected); assert.deepEqual(snapshotMemory(e.data_memory_1), data);
