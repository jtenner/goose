import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';
import { snapshotMemory } from './wasm_memory_snapshot.mjs';
const mode = process.argv[3]; assert(['fixed', 'limited'].includes(mode));
const size = mode === 'fixed' ? 2 : 4, prefix = mode === 'fixed' ? 0 : 1;
let runtime, initial, expected, data, visits = 0;
runtime = instantiate(fs.readFileSync(process.argv[2]), bytes => {
    const label = Buffer.from(bytes).toString('utf8').trim(), e = runtime.instance.exports;
    assert.equal(e.test_stack_top_0.value, initial + 2, 'expression inline live frame top differs');
    assert.equal(e.test_stack_top_1.value, 1, 'expression inline data top differs');
    if (label === 'true') {
        assert.equal(visits++, 0);
        const view = new Uint8Array(e.memory.buffer); view.fill(0xa5, initial + 2, initial + 2 + size); view[initial + 2 + size] = 0x6c;
        let image = snapshotMemory(e.memory), pattern = Buffer.from([7, 8]), payload = image.indexOf(pattern);
        assert(payload >= prefix && payload + 2 <= initial && image.indexOf(pattern, payload + 1) < 0);
        if (prefix) { assert.equal(image[payload - 1], 2); view[payload + 2] = 0xb6; }
        expected = snapshotMemory(e.memory); expected.copy(expected, initial + 2, payload - prefix, payload - prefix + size);
        const target = new Uint8Array(e.data_memory_1.buffer); target.fill(0x5a, 1); target[7] = 0xc5;
        data = snapshotMemory(e.data_memory_1); data.writeUInt32LE(2, 1); data[5] = 7; data[6] = 8;
    } else {
        assert.equal(label, visits++ === 1 ? 'false' : 'opaque');
        assert.deepEqual(snapshotMemory(e.memory), expected, 'expression inline memory 0 image differs');
        assert.deepEqual(snapshotMemory(e.data_memory_1), data, 'expression inline data image differs');
    }
    assert.equal(runtime.pendingPrints, 0); fs.writeSync(1, bytes);
});
initial = runtime.instance.exports.test_stack_top_0.value;
runCompleted(runtime); assert.equal(visits, 3);
const e = runtime.instance.exports;
assert.equal(e.test_stack_top_0.value, initial, 'expression inline completed frame top differs'); assert.equal(e.test_stack_top_1.value, 1);
assert.deepEqual(snapshotMemory(e.memory), expected); assert.deepEqual(snapshotMemory(e.data_memory_1), data);
