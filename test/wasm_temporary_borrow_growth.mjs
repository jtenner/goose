import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';
import { snapshotMemory } from './wasm_memory_snapshot.mjs';
let output = '';
const runtime = instantiate(fs.readFileSync(process.argv[2]), bytes => {
    output += Buffer.from(bytes).toString('utf8');
});
const memory = runtime.instance.exports.memory;
const initial = runtime.instance.exports.test_stack_top_0.value;
new Uint8Array(memory.buffer).fill(0xa5, initial);
const before = snapshotMemory(memory);
runCompleted(runtime);
assert.equal(output, 'growth\n');
assert(memory.buffer.byteLength > before.length, 'temporary borrow frame did not grow memory');
assert.equal(runtime.instance.exports.test_stack_top_0.value, initial,
    'temporary borrow growth frame top differs');
const expected = Buffer.alloc(memory.buffer.byteLength);
before.copy(expected);
expected.writeBigInt64LE(7n, initial);
for (let i = 0; i < 9000; i++) expected.writeBigInt64LE(-23n, initial + 8 + 8 * i);
assert(snapshotMemory(memory).equals(expected), 'temporary borrow growth image differs');
assert.equal(runtime.pendingPrints, 0);
if (process.argv[3]) fs.writeFileSync(process.argv[3], JSON.stringify({ initial,
    before: before.length, after: memory.buffer.byteLength }) + '\n');
fs.writeSync(1, output);
