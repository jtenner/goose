import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';
import { snapshotMemory } from './wasm_memory_snapshot.mjs';
const [file, rawCount, record] = process.argv.slice(2), count = Number(rawCount);
assert([0,127,128,16383,16384].includes(count));
const encoded = []; let remaining = count;
do { const byte = remaining % 128; remaining = Math.floor(remaining / 128); encoded.push(byte | (remaining ? 128 : 0)); } while (remaining);
const prefix = encoded.length, top = 1 + prefix + count * 11;
const cell = Buffer.alloc(11); cell[0] = 34; cell.writeBigInt64LE(-8n,1); cell.writeUInt16LE(900,9);
let runtime, initial, frame, image, seen = 0;
runtime = instantiate(fs.readFileSync(file), bytes => {
    const label = Buffer.from(bytes).toString('utf8').trim(), e = runtime.instance.exports;
    assert.equal(runtime.pendingPrints,0);
    if (label === 'before') {
        assert.equal(seen,0); assert.equal(e.test_stack_top_0.value,initial); assert.equal(e.test_stack_top_1.value,1);
        const pages = Math.ceil((top+1)/65536), old = e.data_memory_1.buffer.byteLength / 65536;
        if (old < pages) e.data_memory_1.grow(pages-old);
        const m0 = new Uint8Array(e.memory.buffer); m0.fill(212,initial,initial+11); m0[initial+11] = 108;
        frame = snapshotMemory(e.memory);
        const data = new Uint8Array(e.data_memory_1.buffer); data.fill(165,1); data[top] = 197;
        image = snapshotMemory(e.data_memory_1); Buffer.from(encoded).copy(image,1);
    } else if (label === 'eval') {
        assert.equal(seen,1,'LEB fill evaluation stage differs');
        assert.equal(e.test_stack_top_0.value,initial+11,'LEB live snapshot top differs');
        assert.equal(e.test_stack_top_1.value,top,'LEB receiving reservation differs');
        frame[initial] = 34;
        assert.deepEqual(snapshotMemory(e.memory),frame,'LEB fill memory 0 image differs');
        assert.deepEqual(snapshotMemory(e.data_memory_1),image,'LEB fill data image differs');
    } else {
        assert.equal(label,'after'); assert.equal(seen,2,'LEB fill initializer checkpoint differs');
        assert.equal(e.test_stack_top_0.value,initial,'LEB snapshot restore differs');
        assert.equal(e.test_stack_top_1.value,top,'LEB receiving top differs');
        cell.copy(frame,initial); for (let i=0;i<count;i++) cell.copy(image,1+prefix+i*11);
        assert.deepEqual(snapshotMemory(e.memory),frame,'LEB fill memory 0 image differs');
        assert.deepEqual(snapshotMemory(e.data_memory_1),image,'LEB fill data image differs');
    }
    seen++; fs.writeSync(1,bytes);
});
initial = runtime.instance.exports.test_stack_top_0.value;
runCompleted(runtime); assert.equal(seen,3);
const e=runtime.instance.exports;
assert.equal(e.test_stack_top_0.value,initial,'LEB completed snapshot top differs');
assert.equal(e.test_stack_top_1.value,1,'LEB completed data top differs');
assert.deepEqual(snapshotMemory(e.memory),frame,'LEB completed memory 0 image differs');
assert.deepEqual(snapshotMemory(e.data_memory_1),image,'LEB completed data image differs');
if(record) fs.writeFileSync(record,JSON.stringify({initial,count,prefix,top}));
