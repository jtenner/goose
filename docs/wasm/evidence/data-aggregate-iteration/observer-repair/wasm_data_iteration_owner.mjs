// Test-only top exports and live checkpoints; no production ABI change.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';
const [file, mode, record] = process.argv.slice(2);
const sizes = { copy: 7, zero: 7, cleanup: 8, enum: 9, inline: 5 };
assert(mode in sizes);
let runtime, x, initial, before, count = 0;
const events = [];
const memory = i => i ? x[`data_memory_${i}`] : x.memory;
const top = i => x[`test_stack_top_${i}`].value;
const int = n => { const b = Buffer.alloc(8); b.writeBigInt64LE(BigInt(n)); return b; };
const row = (mark, n, tail) => { const b = Buffer.alloc(7); b[0] = mark; b.writeUInt32LE(n, 1); b.writeUInt16LE(tail, 5); return b; };
const image = (i, n, payload) => {
    const result = Buffer.alloc(memory(i).buffer.byteLength);
    result.writeUInt32LE(n, 1); payload.copy(result, 5); return result;
};
const checkMemory = (i, expected) => assert.deepEqual(Buffer.from(memory(i).buffer), expected, `complete memory ${i} differs`);
const enumRows = Buffer.concat([Buffer.concat([Buffer.from([0]), int(7)]),
    Buffer.from([1, 1, 2, 3, 199, 199, 199, 199, 199]), Buffer.from([2, 199, 199, 199, 199, 199, 199, 199, 199])]);
const inlineRows = Buffer.from([1, 1, 199, 199, 11, 2, 2, 3, 199, 22]);
runtime = instantiate(fs.readFileSync(file), bytes => {
    const text = Buffer.from(bytes).toString('utf8').trim();
    assert.equal(runtime.pendingPrints, 0);
    assert.equal(top(0), initial + sizes[mode], 'iteration checkpoint is outside its live frame');
    const expected0 = Buffer.from(before);
    assert.deepEqual([...new Uint8Array(x.memory.buffer, initial + sizes[mode], 8)],
        Array(8).fill(166), 'iteration copy crossed its planned owner image');
    if (mode === 'copy') {
        assert.equal(text, 'iteration');
        row((count + 1) * 11, (count + 1) * 100, 50001 + count * 10001).copy(expected0, initial);
        checkMemory(1, image(1, 2, Buffer.concat([row(11, 1100, 50001), row(22, count ? 1200 : 200, 60002)])));
        assert.equal(top(1), 19);
    } else if (mode === 'zero') {
        assert.equal(text, 'empty');
        assert.deepEqual([...new Uint8Array(x.memory.buffer, initial, 7)],
            Array(7).fill(165), 'zero-trip iteration copied an element');
        const expected = image(1, 0, Buffer.alloc(0)); expected.fill(34, 5, 12);
        checkMemory(1, expected); assert.equal(top(1), 5);
    } else if (mode === 'cleanup') {
        assert(['inner', 'restored', 'continue', 'after'].includes(text));
        int(count < 3 ? 1 : 2).copy(expected0, initial);
        assert.equal(top(1), 13, 'live outer data owner was lost');
        assert.equal(top(2), 21, 'live data source was lost');
        assert.equal(top(3), text === 'inner' || text === 'continue' ? 13 : 1,
            'iteration body data top was not restored at its completion');
        checkMemory(1, image(1, 1, int(91)));
        checkMemory(2, image(2, 2, Buffer.concat([int(1), int(2)])));
        checkMemory(3, image(3, 1, int(text === 'continue' ? 8 : 7)));
    } else {
        const isEnum = mode === 'enum'; const stride = sizes[mode];
        if (text === 'seed') {
            assert.equal(count, 0);
            const data = new Uint8Array(memory(1).buffer);
            if (isEnum) { data.fill(199, 18, 23); data.fill(199, 24, 32); }
            else { data.fill(199, 7, 9); data[13] = 199; }
        } else {
            assert.equal(text, isEnum ? 'enumcopy' : 'inlinecopy');
            const source = isEnum ? enumRows : inlineRows;
            source.subarray((count - 1) * stride, count * stride).copy(expected0, initial);
        }
        const source = isEnum ? enumRows : inlineRows;
        checkMemory(1, image(1, isEnum ? 3 : 2, source));
        assert.equal(top(1), 5 + source.length);
    }
    checkMemory(0, expected0);
    events.push(text); count++; fs.writeSync(1, bytes);
});
x = runtime.instance.exports; initial = top(0);
const end = initial + sizes[mode] + 8;
if (end > x.memory.buffer.byteLength) x.memory.grow(Math.ceil((end - x.memory.buffer.byteLength) / 65536));
new Uint8Array(x.memory.buffer).fill(165, initial, initial + sizes[mode]);
new Uint8Array(x.memory.buffer).fill(166, initial + sizes[mode], end);
if (mode === 'zero') new Uint8Array(memory(1).buffer).fill(34, 5, 12);
before = Buffer.from(x.memory.buffer);
const completion = runCompleted(runtime);
assert.equal(top(0), initial, 'iteration activation top was not restored');
for (let i = 1; x[`test_stack_top_${i}`]; i++) assert.equal(top(i), 1, `data top ${i} was not restored`);
const expectedEvents = mode === 'copy' ? ['iteration', 'iteration'] : mode === 'zero' ? ['empty'] :
    mode === 'cleanup' ? ['inner', 'restored', 'continue', 'inner', 'restored', 'after'] :
    mode === 'enum' ? ['seed', 'enumcopy', 'enumcopy', 'enumcopy'] : ['seed', 'inlinecopy', 'inlinecopy'];
assert.deepEqual(events, expectedEvents);
if (record) fs.writeFileSync(record, JSON.stringify({ mode, events, completion, fullMemoryModels: true,
    initial, frameBytes: sizes[mode], complete: true }, null, 2) + '\n');
