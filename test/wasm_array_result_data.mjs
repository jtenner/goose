import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';
import { snapshotMemory } from './wasm_memory_snapshot.mjs';
const [file] = process.argv.slice(2);
const labels = ['row0', 'row1', 'row2', 'data_control'];
const rows = [[90, 4660, 22136, 13124], [91, 7, 8, 21862], [92, 11, 12, 30600]];
let runtime, initial, expected, mainImage, visits = 0;
runtime = instantiate(fs.readFileSync(file), bytes => {
    const label = Buffer.from(bytes).toString('utf8').trim();
    assert.equal(label, labels[visits]);
    const field = visits < 3 ? visits : 2;
    const exports = runtime.instance.exports;
    assert.equal(exports.test_stack_top_0.value, initial[0], 'nested array frame top differs');
    assert.equal(exports.test_stack_top_1.value, initial[1] + 40, 'nested array data top differs');
    assert.equal(exports.test_stack_top_2.value, initial[2], 'nested array scratch top differs');
    if (visits === 0) expected[0].writeUInt32LE(3, initial[1]);
    if (visits < 3) {
        if (visits) expected[0].writeUInt16LE(rows[visits - 1][3], initial[1] + 4 + (visits - 1) * 12 + 10);
        const offset = initial[1] + 4 + visits * 12;
        expected[0][offset] = rows[visits][0];
        expected[0][offset + 1] = 2;
        expected[0].writeUInt16LE(rows[visits][1], offset + 2);
        expected[0].writeUInt16LE(rows[visits][2], offset + 4);
        expected[1].writeUInt32LE(1, initial[2]);
        expected[1].writeUInt16LE(rows[visits][1], initial[2] + 4);
    } else expected[0].writeUInt16LE(rows[field][3], initial[1] + 4 + field * 12 + 10);
    assert.deepEqual(snapshotMemory(exports.memory), mainImage, 'nested array Memory 0 image differs');
    for (let i = 0; i < 2; i++) assert.deepEqual(snapshotMemory(exports[`data_memory_${i + 1}`]), expected[i],
        'nested array data image differs');
    assert.equal(runtime.pendingPrints, 0);
    visits++;
    fs.writeSync(1, bytes);
});
const exports = runtime.instance.exports;
initial = [0, 1, 2].map(i => exports[`test_stack_top_${i}`].value);
mainImage = snapshotMemory(exports.memory);
expected = [1, 2].map((i) => {
    const memory = exports[`data_memory_${i}`];
    if (memory.buffer.byteLength === 0) memory.grow(1);
    new Uint8Array(memory.buffer).fill(i === 1 ? 165 : 90, initial[i]);
    return snapshotMemory(memory);
});
runCompleted(runtime);
assert.equal(visits, 4);
for (let i = 0; i < 3; i++) assert.equal(exports[`test_stack_top_${i}`].value, initial[i]);
assert.deepEqual(snapshotMemory(exports.memory), mainImage);
for (let i = 0; i < 2; i++) assert.deepEqual(snapshotMemory(exports[`data_memory_${i + 1}`]), expected[i]);
