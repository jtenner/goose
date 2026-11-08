import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';
import { snapshotMemory } from './wasm_memory_snapshot.mjs';
const [file, metadata] = process.argv.slice(2);
const image = Buffer.from([2, 0x34, 0x12, 0x78, 0x56, 0, 0, 0, 0]);
const labels = ['seed', 'arg-live', 'callee-live', 'callee-defer', 'done'];
let runtime, initial, expected, source, visits = 0;
runtime = instantiate(fs.readFileSync(file), bytes => {
    const label = Buffer.from(bytes).toString('utf8').trim();
    assert.equal(label, labels[visits++]);
    const top = initial + (label === 'arg-live' ? 9 : label === 'seed' || label === 'done' ? 0 : 18);
    assert.equal(runtime.instance.exports.test_stack_top_0.value, top,
        'array argument live frame top differs');
    const memory = runtime.instance.exports.memory;
    if (label === 'seed') {
        const before = snapshotMemory(memory);
        source = before.subarray(0, initial).indexOf(image);
        assert(source >= 0);
        assert.equal(before.subarray(0, initial).indexOf(image, source + 1), -1);
        const inactive = Buffer.from([0xa0, 0xa1, 0xb0, 0xb1]);
        new Uint8Array(memory.buffer).set(inactive, source + 5);
        inactive.copy(image, 5);
    } else if (label === 'arg-live') {
        const before = snapshotMemory(memory);
        assert.deepEqual(before.subarray(initial, initial + 9), image,
            'array argument snapshot image differs');
        new Uint8Array(memory.buffer)[initial + 18] = 165;
        expected = snapshotMemory(memory);
        expected.writeUInt16LE(12, source + 1);
        image.copy(expected, initial + 9);
    } else {
        if (label === 'callee-defer') expected.writeUInt16LE(9, initial + 12);
        assert.deepEqual(snapshotMemory(memory), expected,
            'array argument callee image differs');
    }
    assert.equal(runtime.pendingPrints, 0);
    fs.writeSync(1, bytes);
});
initial = runtime.instance.exports.test_stack_top_0.value;
runCompleted(runtime);
assert.equal(visits, 5);
assert.equal(runtime.instance.exports.test_stack_top_0.value, initial,
    'array argument frame top was not restored');
assert.deepEqual(snapshotMemory(runtime.instance.exports.memory), expected,
    'array argument completed image differs');
if (metadata) fs.writeFileSync(metadata, JSON.stringify({ source, initial }) + '\n');
