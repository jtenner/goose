import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';
import { snapshotMemory } from './wasm_memory_snapshot.mjs';
const mode = process.argv[3]; assert(['variable', 'runtime'].includes(mode));
const prefix = mode === 'runtime' ? 8 : 4;
let runtime, initial, expected, data, visits = 0;
runtime = instantiate(fs.readFileSync(process.argv[2]), bytes => {
    const label = Buffer.from(bytes).toString('utf8').trim(), e = runtime.instance.exports;
    if (label === 'inside') {
        assert.equal(visits++, 0);
        assert.equal(e.test_stack_top_0.value, initial + 1, 'empty limited source live frame top differs');
        assert.equal(e.test_stack_top_1.value, 1, 'empty limited receiver allocated before source');
        const view = new Uint8Array(e.memory.buffer);
        view[initial] = 0xb6; view[initial + 1] = 0x6c;
        expected = snapshotMemory(e.memory); expected[initial] = 0;
        const target = new Uint8Array(e.data_memory_1.buffer); target.fill(0x5a, 1); target[1 + prefix] = 0xc5;
        data = snapshotMemory(e.data_memory_1); data.fill(0, 1, 1 + prefix);
    } else {
        assert.equal(label, 'zero_call_' + mode); assert.equal(visits++, 1);
        assert.equal(e.test_stack_top_0.value, initial, 'empty limited source temporary was not released');
        assert.equal(e.test_stack_top_1.value, 1 + prefix, 'empty limited receiver was released early');
        assert.deepEqual(snapshotMemory(e.memory), expected, 'empty limited receiver memory 0 image differs');
        assert.deepEqual(snapshotMemory(e.data_memory_1), data, 'empty limited receiver data image differs');
    }
    assert.equal(runtime.pendingPrints, 0); fs.writeSync(1, bytes);
});
initial = runtime.instance.exports.test_stack_top_0.value;
runCompleted(runtime); assert.equal(visits, 2);
const e = runtime.instance.exports;
assert.equal(e.test_stack_top_0.value, initial, 'empty limited completed frame top differs');
assert.equal(e.test_stack_top_1.value, 1, 'empty limited completed data top differs');
assert.deepEqual(snapshotMemory(e.memory), expected); assert.deepEqual(snapshotMemory(e.data_memory_1), data);
