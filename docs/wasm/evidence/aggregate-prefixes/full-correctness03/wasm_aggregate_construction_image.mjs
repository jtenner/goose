import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';
import { snapshotMemory } from './wasm_memory_snapshot.mjs';
const [file] = process.argv.slice(2);
let runtime, initial, expected, target, seen = 0;
runtime = instantiate(fs.readFileSync(file), bytes => {
    const line = Buffer.from(bytes).toString('utf8').trim();
    const memory = runtime.instance.exports.memory;
    assert.equal(runtime.pendingPrints, 0);
    if (line === 'seed') {
        assert.equal(seen, 0);
        assert.equal(runtime.instance.exports.test_stack_top_0.value, initial);
        expected = snapshotMemory(memory);
        const original = Buffer.alloc(13);
        original[0] = 129; original.writeUInt16LE(58099, 11);
        const locations = [];
        for (let i = 0; i <= initial - original.length; i++)
            if (expected.subarray(i, i + 13).equals(original)) locations.push(i);
        assert.equal(locations.length, 1, 'aggregate image target is not unique');
        [target] = locations;
    } else if (line === 'eval') {
        assert.equal(seen, 1);
        assert.equal(runtime.instance.exports.test_stack_top_0.value, initial + 16);
        assert.deepEqual(snapshotMemory(memory).subarray(0, initial), expected.subarray(0, initial),
            'unfinished aggregate construction changed permanent Memory 0');
        const view = new Uint8Array(memory.buffer);
        assert.equal(view[initial], 17);
        assert.equal(view[initial + 1], 2);
        assert.equal(view[initial + 13], 34);
        // These are valid reserved, not yet initialized payload bytes.
        view.fill(167, initial + 2, initial + 11);
        expected = snapshotMemory(memory);
        const cell = Buffer.from([34, 103, 69]);
        cell.copy(expected, initial + 13);
        cell.copy(expected, initial + 2);
        cell.copy(expected, initial + 5);
        expected.writeUInt16LE(31355, initial + 11);
        expected.subarray(initial, initial + 13).copy(expected, target);
    } else {
        assert.equal(line, 'filled');
        assert.equal(seen, 2);
        assert.equal(runtime.instance.exports.test_stack_top_0.value, initial);
        assert.deepEqual(snapshotMemory(memory), expected, 'aggregate fill complete Memory 0 image differs');
    }
    seen++; fs.writeSync(1, bytes);
});
initial = runtime.instance.exports.test_stack_top_0.value;
runCompleted(runtime);
assert.equal(seen, 3);
assert.equal(runtime.instance.exports.test_stack_top_0.value, initial);
assert.deepEqual(snapshotMemory(runtime.instance.exports.memory), expected,
    'aggregate fill completed Memory 0 image differs');
