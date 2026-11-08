import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';
import { snapshotMemory } from './wasm_memory_snapshot.mjs';
const [file, metadata] = process.argv.slice(2);
const image = Buffer.from([2, 0x34, 0x12, 0x78, 0x56, 0, 0, 0, 0]);
const oldTarget = Buffer.from([1, 1, 0, 0, 0, 0, 0, 0, 0]);
const labels = ['before', 'arg-live', 'callee-live', 'defer', 'after'];
let runtime, initial, expected, source, target, visits = 0;
runtime = instantiate(fs.readFileSync(file), bytes => {
    const label = Buffer.from(bytes).toString('utf8').trim();
    assert.equal(label, labels[visits++]);
    const top = initial + (label === 'arg-live' ? 18 : label === 'before' || label === 'after' ? 0 : 36);
    assert.equal(runtime.instance.exports.test_stack_top_0.value, top,
        'array result live frame top differs');
    const memory = runtime.instance.exports.memory;
    if (label === 'before') {
        const before = snapshotMemory(memory);
        source = before.subarray(0, initial).indexOf(image);
        target = before.subarray(0, initial).indexOf(oldTarget);
        assert(source >= 0 && target >= 0 && source !== target);
        assert.equal(before.subarray(0, initial).indexOf(image, source + 1), -1);
        assert.equal(before.subarray(0, initial).indexOf(oldTarget, target + 1), -1);
        const inactive = Buffer.from([0xa0, 0xa1, 0xb0, 0xb1]);
        new Uint8Array(memory.buffer).set(inactive, source + 5);
        inactive.copy(image, 5);
    } else if (label === 'arg-live') {
        const before = snapshotMemory(memory);
        assert.deepEqual(before.subarray(initial + 9, initial + 18), image);
        new Uint8Array(memory.buffer).fill(165, initial, initial + 9);
        new Uint8Array(memory.buffer)[initial + 36] = 90;
        expected = snapshotMemory(memory);
        expected.writeUInt16LE(12, source + 1);
        image.copy(expected, initial + 18);
        image.copy(expected, initial + 27);
    } else {
        if (label === 'defer') {
            image.copy(expected, initial);
            expected.writeUInt16LE(9, initial + 30);
        }
        if (label === 'after') image.copy(expected, target);
        assert.deepEqual(snapshotMemory(memory), expected,
            'array result protected image differs');
    }
    assert.equal(runtime.pendingPrints, 0);
    fs.writeSync(1, bytes);
});
initial = runtime.instance.exports.test_stack_top_0.value;
runCompleted(runtime);
assert.equal(visits, 5);
assert.equal(runtime.instance.exports.test_stack_top_0.value, initial,
    'array result frame top was not restored');
assert.deepEqual(snapshotMemory(runtime.instance.exports.memory), expected,
    'array result completed image differs');
if (metadata) fs.writeFileSync(metadata, JSON.stringify({ source, target, initial }) + '\n');
