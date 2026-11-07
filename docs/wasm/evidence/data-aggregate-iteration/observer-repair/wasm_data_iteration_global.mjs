// Derived test exports expose tops. Globals remain live after guest completion.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';
const [file, width, amount, resultFile] = process.argv.slice(2);
const stride = Number(width), count = Number(amount);
assert([1, 7, 16, 256, 40008].includes(stride));
const row = Buffer.alloc(stride, stride > 16 ? 3 : 0);
if (stride === 7) { row[0] = 11; row.writeUInt32LE(7, 1); row.writeUInt16LE(50001, 5); }
else if (stride === 16) { row.writeBigInt64LE(7n, 0); row.writeBigInt64LE(9n, 8); }
else if (stride > 16) row.writeBigInt64LE(7n, stride - 8);
const runtime = instantiate(fs.readFileSync(file), bytes => fs.writeSync(1, bytes));
const x = runtime.instance.exports;
const initial = x.test_stack_top_0.value;
const before = Buffer.from(x.memory.buffer);
const completion = runCompleted(runtime);
assert.equal(x.test_stack_top_0.value, initial, 'copied loop frame was not restored');
assert.equal(x.test_stack_top_1.value, 5 + count * stride, 'persistent source top is wrong');
const expected0 = Buffer.alloc(x.memory.buffer.byteLength); before.copy(expected0);
row.copy(expected0, 8);
expected0.writeBigInt64LE((1n << 32n) | 1n, 8 + stride);
if (count) row.copy(expected0, initial);
assert.deepEqual(Buffer.from(x.memory.buffer), expected0, 'complete global/frame image differs');
const expected1 = Buffer.alloc(x.data_memory_1.buffer.byteLength);
expected1.writeUInt32LE(count, 1);
for (let i = 0; i < count; i++) row.copy(expected1, 5 + i * stride);
assert.deepEqual(Buffer.from(x.data_memory_1.buffer), expected1, 'complete data source image differs');
if (resultFile) fs.writeFileSync(resultFile, JSON.stringify({ stride, count, initial,
    binderBytes: stride, sourceTop: x.test_stack_top_1.value, completion,
    memory0Pages: x.memory.buffer.byteLength / 65536,
    dataPages: x.data_memory_1.buffer.byteLength / 65536,
    completeImages: true }, null, 2) + '\n');
