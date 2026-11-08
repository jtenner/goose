import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';
import { snapshotMemory } from './wasm_memory_snapshot.mjs';
const runtime = instantiate(fs.readFileSync(process.argv[2]), bytes => fs.writeSync(1, bytes));
const initial = runtime.instance.exports.test_stack_top_0.value;
const expected = snapshotMemory(runtime.instance.exports.data_memory_1);
expected.writeUInt32LE(2, 1); expected.writeBigInt64LE(10n, 5); expected.writeBigInt64LE(20n, 13);
runCompleted(runtime);
assert.equal(runtime.instance.exports.test_stack_top_0.value, initial);
assert.equal(runtime.instance.exports.test_stack_top_1.value, 21, 'zero call global data top differs');
assert.deepEqual(snapshotMemory(runtime.instance.exports.data_memory_1), expected,
    'zero call global data image differs');
assert.equal(runtime.instance.exports.data_memory_2, undefined);
