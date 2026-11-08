import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';
import { snapshotMemory } from './wasm_memory_snapshot.mjs';
let runtime, frame, source, target, initial, visits = 0;
runtime = instantiate(fs.readFileSync(process.argv[2]), bytes => {
    const label = Buffer.from(bytes).toString('utf8').trim(), e = runtime.instance.exports;
    assert.equal(e.test_stack_top_0.value, initial, 'limited data frame top differs');
    assert.equal(e.test_stack_top_1.value, 12, 'limited data source top differs');
    assert.equal(e.test_stack_top_2.value, 266, 'limited data target top differs');
    if (label === 'before') {
        assert.equal(visits++, 0);
        const view = new Uint8Array(e.data_memory_2.buffer);
        view.fill(0xa5, 6, 264); view.fill(0xd3, 264, 266); view[266] = 0xc5;
        frame = snapshotMemory(e.memory); source = snapshotMemory(e.data_memory_1);
        assert.equal(source[6], 2); assert.deepEqual([...source.subarray(7, 9)], [7, 8]);
        target = snapshotMemory(e.data_memory_2); target.writeUInt16LE(2, 6);
        target[8] = 7; target[9] = 8; target.writeUInt16LE(65000, 264);
    } else {
        assert.equal(label, 'after'); assert.equal(visits++, 1);
        assert.deepEqual(snapshotMemory(e.memory), frame, 'limited data memory 0 image differs');
        assert.deepEqual(snapshotMemory(e.data_memory_1), source, 'limited data source image differs');
        assert.deepEqual(snapshotMemory(e.data_memory_2), target, 'limited data target image differs');
    }
    assert.equal(runtime.pendingPrints, 0); fs.writeSync(1, bytes);
});
initial = runtime.instance.exports.test_stack_top_0.value;
runCompleted(runtime); assert.equal(visits, 2);
const e = runtime.instance.exports;
assert.equal(e.test_stack_top_0.value, initial);
assert.equal(e.test_stack_top_1.value, 1); assert.equal(e.test_stack_top_2.value, 1);
assert.deepEqual(snapshotMemory(e.memory), frame);
assert.deepEqual(snapshotMemory(e.data_memory_1), source);
assert.deepEqual(snapshotMemory(e.data_memory_2), target);
