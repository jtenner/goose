import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';
import { snapshotMemory } from './wasm_memory_snapshot.mjs';
const capacity = Number(process.argv[3]);
assert([255, 256, 65535, 65536].includes(capacity));
const prefix = capacity <= 255 ? 1 : capacity <= 65535 ? 2 : 4;
const image = prefix + capacity * 4;
const pattern = Buffer.alloc(8);
pattern.writeInt32LE(19088743); pattern.writeInt32LE(-19088743, 4);
let runtime, initial, expected, visits = 0;
runtime = instantiate(fs.readFileSync(process.argv[2]), bytes => {
    assert.equal(runtime.instance.exports.test_stack_top_0.value, initial + image,
        'adapted negation prefix live frame top differs');
    const label = Buffer.from(bytes).toString('utf8').trim();
    const memory = runtime.instance.exports.memory;
    if (visits++ === 0) {
        assert.equal(label, 'before');
        const before = snapshotMemory(memory);
        assert(before.subarray(0, initial).indexOf(pattern) >= 0);
        new Uint8Array(memory.buffer).fill(0xa5, initial, initial + image);
        new Uint8Array(memory.buffer)[initial + image] = 0x5a;
        expected = snapshotMemory(memory);
        expected.writeUIntLE(2, initial, prefix);
        expected.writeInt32LE(-19088743, initial + prefix);
        expected.writeInt32LE(19088743, initial + prefix + 4);
    } else {
        assert.deepEqual(snapshotMemory(memory), expected, 'adapted negation prefix memory image differs');
        assert.equal(label, 'after=2,-19088743,19088743');
    }
    assert.equal(runtime.pendingPrints, 0);
    fs.writeSync(1, bytes);
});
initial = runtime.instance.exports.test_stack_top_0.value;
runCompleted(runtime);
assert.equal(visits, 2);
assert.equal(runtime.instance.exports.test_stack_top_0.value, initial);
assert.deepEqual(snapshotMemory(runtime.instance.exports.memory), expected);
