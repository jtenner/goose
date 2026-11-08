import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';
import { snapshotMemory } from './wasm_memory_snapshot.mjs';
const mode = process.argv[3]; assert(['fixed', 'limited'].includes(mode));
const size = mode === 'fixed' ? 2 : 4, prefix = mode === 'fixed' ? 0 : 1;
let runtime, initial, expected, data, payload, visits = 0;
runtime = instantiate(fs.readFileSync(process.argv[2]), bytes => {
    const label = Buffer.from(bytes).toString('utf8').trim(), e = runtime.instance.exports;
    if (label === 'inside') {
        assert.equal(visits++, 0);
        assert.equal(e.test_stack_top_0.value, initial + size, 'expression source reservation differs');
        assert.equal(e.test_stack_top_1.value, 1, 'expression receiver allocated before source');
        const view = new Uint8Array(e.memory.buffer); view.fill(0xa5, initial, initial + size); view[initial + size] = 0x6c;
        let image = snapshotMemory(e.memory), pattern = Buffer.from([209, 226]); payload = image.indexOf(pattern);
        assert(payload >= prefix && payload + 2 <= initial && image.indexOf(pattern, payload + 1) < 0);
        if (prefix) { assert.equal(image[payload - 1], 2); view[payload + 2] = 0xb6; }
        expected = snapshotMemory(e.memory); expected.copy(expected, initial, payload - prefix, payload - prefix + size);
        expected[payload] = 99;
        const target = new Uint8Array(e.data_memory_1.buffer); target.fill(0x5a, 1); target[7] = 0xc5;
        data = snapshotMemory(e.data_memory_1); data.writeUInt32LE(2, 1); data[5] = 209; data[6] = 226;
    } else {
        assert.equal(label, 'after'); assert.equal(visits++, 1);
        assert.equal(e.test_stack_top_0.value, initial, 'expression source temporary was not released');
        assert.equal(e.test_stack_top_1.value, 7, 'expression receiver was released early');
        assert.deepEqual(snapshotMemory(e.memory), expected, 'expression memory 0 image differs');
        assert.deepEqual(snapshotMemory(e.data_memory_1), data, 'expression data image differs');
    }
    assert.equal(runtime.pendingPrints, 0); fs.writeSync(1, bytes);
});
initial = runtime.instance.exports.test_stack_top_0.value;
runCompleted(runtime); assert.equal(visits, 2);
const e = runtime.instance.exports;
assert.equal(e.test_stack_top_0.value, initial); assert.equal(e.test_stack_top_1.value, 1, 'expression completed data top differs');
assert.deepEqual(snapshotMemory(e.memory), expected); assert.deepEqual(snapshotMemory(e.data_memory_1), data);
if (process.argv[4]) fs.writeFileSync(process.argv[4], JSON.stringify({payload, initial, size}));
