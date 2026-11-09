// Complete Memory 0 model for a borrowed packed field across a later call.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';
import { snapshotMemory } from './wasm_memory_snapshot.mjs';
const [file, metadata] = process.argv.slice(2);
const labels = ['before', 'argument-live', 'callee-live', 'after',
    'argument-live', 'callee-live', 'after'];
let runtime, initial, expected, visits = 0;
runtime = instantiate(fs.readFileSync(file), bytes => {
    const label = Buffer.from(bytes).toString('utf8').trim();
    assert.equal(label, labels[visits++]);
    const delta = label === 'argument-live' ? 22 : label === 'callee-live' ? 11 : 0;
    assert.equal(runtime.instance.exports.test_stack_top_0.value, initial + delta,
        'temporary borrow live frame top differs');
    const memory = runtime.instance.exports.memory;
    if (label === 'before') {
        new Uint8Array(memory.buffer).fill(0xa5, initial);
        expected = snapshotMemory(memory);
        expected[initial] = 17;
        expected.writeBigInt64LE(700n, initial + 1);
        expected.writeUInt16LE(4660, initial + 9);
        expected[initial + 11] = 99;
        expected.writeBigInt64LE(-77n, initial + 12);
        expected.writeUInt16LE(88, initial + 20);
    } else {
        assert(snapshotMemory(memory).equals(expected), 'temporary borrow complete image differs');
    }
    assert.equal(runtime.pendingPrints, 0);
    fs.writeSync(1, bytes);
});
initial = runtime.instance.exports.test_stack_top_0.value;
runCompleted(runtime);
assert.equal(visits, labels.length);
assert.equal(runtime.instance.exports.test_stack_top_0.value, initial,
    'temporary borrow completed frame top differs');
assert(snapshotMemory(runtime.instance.exports.memory).equals(expected),
    'temporary borrow completed image differs');
if (metadata) fs.writeFileSync(metadata, JSON.stringify({ initial }) + '\n');
