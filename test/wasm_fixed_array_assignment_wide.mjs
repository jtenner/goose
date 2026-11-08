import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';
import { snapshotMemory } from './wasm_memory_snapshot.mjs';
let runtime, initial, expected, visits = 0;
runtime = instantiate(fs.readFileSync(process.argv[2]), bytes => {
    const label = Buffer.from(bytes).toString('utf8').trim();
    assert.equal(runtime.instance.exports.test_stack_top_0.value, initial + 516, 'wide array assignment live frame top differs');
    if (label === 'before') {
        assert.equal(visits++, 0);
        const view = new Uint8Array(runtime.instance.exports.memory.buffer);
        view.fill(0xa5, initial + 261, initial + 516); view[initial + 516] = 0x6c;
        expected = snapshotMemory(runtime.instance.exports.memory);
        assert(expected.subarray(initial, initial + 256).every(x => x === 7));
        assert.deepEqual([...expected.subarray(initial + 256, initial + 258)], [9, 10]);
        assert.equal(expected.readUInt16LE(initial + 258), 1); assert.equal(expected[initial + 260], 1);
        expected.writeUInt16LE(256, initial + 258); expected.fill(7, initial + 260, initial + 516);
    } else if (label === 'wide') {
        assert.equal(visits++, 1);
        assert.deepEqual(snapshotMemory(runtime.instance.exports.memory), expected, 'wide array assignment memory 0 image differs');
        expected.writeUInt16LE(2, initial + 258); expected[initial + 260] = 9; expected[initial + 261] = 10;
    } else {
        assert.equal(label, 'after'); assert.equal(visits++, 2);
        assert.deepEqual(snapshotMemory(runtime.instance.exports.memory), expected, 'wide array assignment memory 0 image differs');
    }
    assert.equal(runtime.pendingPrints, 0); fs.writeSync(1, bytes);
});
initial = runtime.instance.exports.test_stack_top_0.value;
runCompleted(runtime); assert.equal(visits, 3);
assert.equal(runtime.instance.exports.test_stack_top_0.value, initial, 'wide array assignment completed frame top differs');
assert.deepEqual(snapshotMemory(runtime.instance.exports.memory), expected);
