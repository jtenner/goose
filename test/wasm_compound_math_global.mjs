import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';
import { snapshotMemory } from './wasm_memory_snapshot.mjs';
const runtime = instantiate(fs.readFileSync(process.argv[2]), bytes => fs.writeSync(1, bytes));
const initial = runtime.instance.exports.test_stack_top_0.value;
const expected = snapshotMemory(runtime.instance.exports.data_memory_1);
expected.writeUInt32LE(2, 1);
for (const [i, n] of [10n, -4n, 40n, 50n].entries()) expected.writeBigInt64LE(n, 5 + 8 * i);
runCompleted(runtime);
assert.equal(runtime.instance.exports.test_stack_top_0.value, initial);
assert.equal(runtime.instance.exports.test_stack_top_1.value, 37, 'compound global data top differs');
assert.deepEqual(snapshotMemory(runtime.instance.exports.data_memory_1), expected,
    'compound global data image differs');
