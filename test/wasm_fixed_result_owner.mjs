import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';
import { snapshotMemory } from './wasm_memory_snapshot.mjs';
const [file, metadata] = process.argv.slice(2);
const original = Buffer.alloc(9);
original[0] = 90;
original.writeBigInt64LE(72623859790382856n, 1);
const returned = Buffer.from(original);
returned.writeBigInt64LE(72623859790382857n, 1);
const labels = ['before', 'arg-live', 'callee-live', 'defer', 'after'];
let runtime, initial, expected, target, visits = 0;
runtime = instantiate(fs.readFileSync(file), bytes => {
    const label = Buffer.from(bytes).toString('utf8').trim();
    assert.equal(label, labels[visits++]);
    const extra = label === 'arg-live' ? 18 : ['callee-live', 'defer'].includes(label) ? 36 : 0;
    assert.equal(runtime.instance.exports.test_stack_top_0.value, initial + extra,
        'fixed result live frame top differs');
    const memory = runtime.instance.exports.memory;
    if (label === 'before') {
        expected = snapshotMemory(memory);
        target = expected.subarray(0, initial).indexOf(original);
        assert(target >= 0);
        assert.equal(expected.subarray(0, initial).indexOf(original, target + 1), -1);
    } else if (label === 'arg-live') {
        original.copy(expected, initial + 9);
        assert.deepEqual(snapshotMemory(memory), expected,
            'fixed result argument snapshot differs');
        new Uint8Array(memory.buffer).fill(165, initial, initial + 9);
        new Uint8Array(memory.buffer)[initial + 36] = 165;
        expected.fill(165, initial, initial + 9);
        expected[initial + 36] = 165;
        original.copy(expected, initial + 18);
        returned.copy(expected, initial + 27);
    } else {
        if (label === 'defer') {
            returned.copy(expected, initial);
            expected.writeBigInt64LE(9n, initial + 28);
        }
        if (label === 'after') returned.copy(expected, target);
        assert.deepEqual(snapshotMemory(memory), expected,
            'fixed result protected image differs');
    }
    assert.equal(runtime.pendingPrints, 0);
    fs.writeSync(1, bytes);
});
initial = runtime.instance.exports.test_stack_top_0.value;
runCompleted(runtime);
assert.equal(visits, 5);
assert.equal(runtime.instance.exports.test_stack_top_0.value, initial);
assert.deepEqual(snapshotMemory(runtime.instance.exports.memory), expected,
    'fixed result completed image differs');
if (metadata) fs.writeFileSync(metadata, JSON.stringify({ target, initial }) + '\n');
