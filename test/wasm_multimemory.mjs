// Observe completed guest ownership directly through derived test exports.
// Production modules expose memories, not mutable stack tops.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate, GooseFailure } from '../scripts/run_wasm.mjs';

const bytes = fs.readFileSync(process.argv[2]);
let cursor = 8;
const read = () => {
    let value = 0, shift = 0, byte;
    do { byte = bytes[cursor++]; value += (byte & 127) * 2 ** shift; shift += 7; } while (byte & 128);
    return value;
};
const encode = value => {
    const result = [];
    do { const b = value % 128; value = Math.floor(value / 128); result.push(b | (value ? 128 : 0)); } while (value);
    return result;
};
let memories = 0;
const sections = [];
while (cursor < bytes.length) {
    const id = bytes[cursor++], length = read(), start = cursor, end = start + length;
    if (id === 5) memories = read();
    sections.push({ id, start, end });
    cursor = end;
}
assert(memories >= 1);
if (process.argv[4] === 'no-data') assert.equal(memories, 1, 'array interfaces added an unused data memory');
else assert(memories >= 2);
const output = [...bytes.subarray(0, 8)];
for (const { id, start, end } of sections) {
    let body = [...bytes.subarray(start, end)];
    if (id === 7) {
        cursor = start;
        const count = read(), old = bytes.subarray(cursor, end);
        body = [...encode(count + memories), ...old];
        for (let i = 0; i < memories; i++) {
            const name = Buffer.from(`test_stack_top_${i}`);
            body.push(...encode(name.length), ...name, 3, ...encode(i));
        }
    }
    output.push(id, ...encode(body.length));
    for (const byte of body) output.push(byte);
}
const runtime = instantiate(new Uint8Array(output), buffer => fs.writeSync(1, buffer));
const initialFrameTop = runtime.instance.exports.test_stack_top_0.value;
if (process.argv[4] === 'allocation-failure') {
    assert.throws(() => runtime.run(), error => error instanceof GooseFailure &&
                  error.message.includes('out of memory growing data storage'));
} else runtime.run();
const exports = runtime.instance.exports;
assert.equal(runtime.pendingPrints, 0);
assert.equal(exports.test_stack_top_0.value, initialFrameTop, 'activation frame top was not restored');
const memoriesAfter = [exports.memory];
for (let i = 1; i < memories; i++) memoriesAfter.push(exports[`data_memory_${i}`]);
assert.equal(new Set(memoriesAfter.map(memory => memory.buffer)).size, memories);
// The operation completion is _start's return. Only then inspect the
// resource owner's current top. Scoped stacks must have their saved top.
const persistent = Number(process.argv[3] ?? 0);
for (let i = 1; i < memories - persistent; i++)
    assert.equal(exports[`test_stack_top_${i}`].value, 1, `data stack ${i} was not restored`);
if (process.argv[4] === 'growth')
    assert(memoriesAfter.slice(1).filter(memory => memory.buffer.byteLength >= 131072).length >= 2);
if (process.argv[4] === 'reuse')
    assert.equal(exports.data_memory_1.buffer.byteLength, 131072, 'scoped stack storage accumulated across iterations');
if (process.argv[4] === 'typed-reuse')
    assert.equal(memories, 2, 'sequential type classes did not reuse one logical stack');

if (process.argv[4] === 'variable-reuse')
    for (const memory of memoriesAfter.slice(1))
        assert.equal(memory.buffer.byteLength, 65536, 'small variable allocations accumulated across scopes');

if (process.argv[4] === 'variable-growth')
    assert(memoriesAfter.slice(1).some(memory => memory.buffer.byteLength >= 131072), 'variable payload did not grow its data memory');

if (process.argv[4] === 'allocation-failure')
    for (const memory of memoriesAfter.slice(1))
        assert.equal(memory.buffer.byteLength, 65536, 'overflow attempted a data memory growth');
