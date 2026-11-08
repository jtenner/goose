import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';
import { snapshotMemory } from './wasm_memory_snapshot.mjs';
const [file] = process.argv.slice(2);
let runtime, initial, expected, seen = 0;
runtime = instantiate(fs.readFileSync(file), bytes => {
    const line = Buffer.from(bytes).toString('utf8').trim();
    const memory = runtime.instance.exports.memory;
    assert.equal(runtime.instance.exports.test_stack_top_0.value, initial + 20);
    assert.equal(runtime.pendingPrints, 0);
    if (line === 'seed') {
        assert.equal(seen, 0);
        const image = Buffer.alloc(20);
        image[0] = 1; image.writeUInt16LE(1, 1);
        image[9] = 2; image.writeUInt16LE(7, 10); image.writeUInt16LE(8, 12);
        image.writeUInt16LE(13124, 18);
        image.copy(expected, initial);
        assert.deepEqual(snapshotMemory(memory), expected, 'array image setup differs');
        new Uint8Array(memory.buffer).fill(165, initial + 14, initial + 18);
        expected.fill(165, initial + 14, initial + 18);
    } else {
        assert.equal(line, 'copied'); assert.equal(seen, 1);
        Buffer.from(expected.subarray(initial + 9, initial + 18)).copy(expected, initial);
        assert.deepEqual(snapshotMemory(memory), expected, 'exact array assignment Memory 0 image differs');
    }
    seen++; fs.writeSync(1, bytes);
});
initial = runtime.instance.exports.test_stack_top_0.value;
expected = snapshotMemory(runtime.instance.exports.memory);
runCompleted(runtime);
assert.equal(seen, 2);
assert.equal(runtime.instance.exports.test_stack_top_0.value, initial);
assert.deepEqual(snapshotMemory(runtime.instance.exports.memory), expected,
    'completed array assignment Memory 0 image differs');
