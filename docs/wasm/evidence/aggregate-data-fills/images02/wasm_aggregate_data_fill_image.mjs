import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';
import { snapshotMemory } from './wasm_memory_snapshot.mjs';
const [file, mode, record] = process.argv.slice(2);
const dynamic = mode === 'dynamic';
const match = dynamic ? null : /^u(8|16|32|64)_count(0|3)$/.exec(mode);
assert(dynamic || match, 'unknown fill image mode');
const prefix = dynamic ? 2 : Number(match[1]) / 8;
const count = dynamic ? 3 : Number(match[2]);
const top = 1 + prefix + count * 11;
const cell = Buffer.alloc(11); cell[0] = 34; cell.writeBigInt64LE(-8n, 1); cell.writeUInt16LE(900, 9);
let runtime, initial, expectedFrame, images = [], selected = 1, cycle = 0, stage = 'before', visits = 0;
const memory = (e, i) => i ? e[`data_memory_${i}`] : e.memory;
const checkImages = e => {
    assert.deepEqual(snapshotMemory(e.memory), expectedFrame, 'data fill memory 0 image differs');
    for (let i = 1; i <= (dynamic ? 2 : 1); i++)
        assert.deepEqual(snapshotMemory(memory(e, i)), images[i], 'data fill receiver image differs');
};
runtime = instantiate(fs.readFileSync(file), bytes => {
    const line = Buffer.from(bytes).toString('utf8').trim(), e = runtime.instance.exports;
    if (line === 'before') {
        assert.equal(stage, 'before'); assert.equal(e.test_stack_top_0.value, initial, 'data fill initial frame top differs');
        selected = cycle + 1;
        assert.equal(e.test_stack_top_1.value, cycle ? 6 : 1, 'data fill caller top differs');
        if (dynamic) assert.equal(e.test_stack_top_2.value, 1, 'data fill future top differs');
        for (let i = 1; i <= (dynamic ? 2 : 1); i++) if (!memory(e, i).buffer.byteLength) memory(e, i).grow(1);
        if (cycle) {
            const caller = snapshotMemory(e.data_memory_1);
            assert.equal(caller.readUInt32LE(1), 1); assert.equal(caller[5], 91);
            new Uint8Array(e.data_memory_1.buffer).fill(212, 6);
        }
        const frame = new Uint8Array(e.memory.buffer);
        frame.fill(212, initial, initial + 11); frame[initial + 11] = 108;
        expectedFrame = snapshotMemory(e.memory);
        const target = new Uint8Array(memory(e, selected).buffer);
        target.fill(165, 1); target[top] = 197;
        for (let i = 1; i <= (dynamic ? 2 : 1); i++) images[i] = snapshotMemory(memory(e, i));
        if (prefix === 8) images[selected].writeBigUInt64LE(BigInt(count), 1);
        else images[selected].writeUIntLE(count, 1, prefix);
        stage = 'eval';
    } else if (line === 'eval') {
        assert.equal(stage, 'eval', 'data fill evaluation stage differs');
        assert.equal(e.test_stack_top_0.value, initial + 11, 'data fill live snapshot top differs');
        assert.equal(e[`test_stack_top_${selected}`].value, top, 'data fill live receiver top differs');
        expectedFrame[initial] = 34;
        checkImages(e); stage = 'after';
    } else if (line === 'after') {
        assert.equal(stage, 'after', 'data fill initializer checkpoint differs');
        assert.equal(e.test_stack_top_0.value, initial, 'data fill snapshot restore differs');
        assert.equal(e[`test_stack_top_${selected}`].value, top, 'data fill receiving top differs');
        cell.copy(expectedFrame, initial);
        for (let i = 0; i < count; i++) cell.copy(images[selected], 1 + prefix + i * 11);
        checkImages(e); stage = dynamic ? (cycle ? 'done' : 'between') : 'complete';
    } else {
        assert(dynamic); assert.equal(line, stage);
        assert.equal(e.test_stack_top_0.value, initial, 'data fill completed snapshot top differs');
        assert.equal(e.test_stack_top_1.value, cycle ? 6 : 1, 'data fill completed caller top differs');
        assert.equal(e.test_stack_top_2.value, 1, 'data fill completed receiver top differs');
        checkImages(e);
        if (line === 'between') { cycle++; stage = 'before'; } else stage = 'complete';
    }
    visits++; assert.equal(runtime.pendingPrints, 0); fs.writeSync(1, bytes);
});
initial = runtime.instance.exports.test_stack_top_0.value;
runCompleted(runtime); assert.equal(stage, 'complete'); assert.equal(visits, dynamic ? 8 : 3);
const e = runtime.instance.exports;
assert.equal(e.test_stack_top_0.value, initial, 'data fill final frame top differs');
for (let i = 1; i <= (dynamic ? 2 : 1); i++) assert.equal(e[`test_stack_top_${i}`].value, 1, 'data fill final data top differs');
checkImages(e);
if (record) fs.writeFileSync(record, JSON.stringify({initial, prefix, count, top, frameBytes: 11}));
