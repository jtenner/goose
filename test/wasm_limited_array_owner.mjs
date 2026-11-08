import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';
import { snapshotMemory } from './wasm_memory_snapshot.mjs';
let runtime, initial, expected, visits = 0;
runtime = instantiate(fs.readFileSync(process.argv[2]), bytes => {
    const label = Buffer.from(bytes).toString('utf8').trim();
    assert.equal(runtime.instance.exports.test_stack_top_0.value, initial + 114,
        'limited layout live frame top differs');
    if (label === 'before') {
        assert.equal(visits++, 0);
        const view = new Uint8Array(runtime.instance.exports.memory.buffer);
        view.set([0xc1, 0xd1], initial + 5); view.set([0xc2, 0xd2], initial + 19);
        view.fill(0xb6, initial + 29, initial + 43);
        view.fill(0xa5, initial + 43, initial + 114); view[initial + 114] = 0x6c;
        expected = snapshotMemory(runtime.instance.exports.memory);
        assert.equal(expected[initial], 2);
        expected.copy(expected, initial + 44, initial + 1, initial + 29);
        expected[initial + 43] = 2;
    } else {
        assert.equal(label, 'after'); assert.equal(visits++, 1);
        assert.deepEqual(snapshotMemory(runtime.instance.exports.memory), expected,
            'limited layout memory 0 image differs');
    }
    assert.equal(runtime.pendingPrints, 0); fs.writeSync(1, bytes);
});
initial = runtime.instance.exports.test_stack_top_0.value;
runCompleted(runtime); assert.equal(visits, 2);
assert.equal(runtime.instance.exports.test_stack_top_0.value, initial, 'limited layout completed frame top differs');
assert.deepEqual(snapshotMemory(runtime.instance.exports.memory), expected);
