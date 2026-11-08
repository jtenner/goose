import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';
import { snapshotMemory } from './wasm_memory_snapshot.mjs';
const mode = process.argv[3];
assert(['variable', 'varint', 'limited', 'grow', 'stored'].includes(mode));
const frame = mode === 'grow' ? 48 : 32;
const prefix = mode === 'grow' ? 0 : mode === 'limited' ? 8 : mode === 'varint' ? 1 : 4;
const end = 1 + prefix + 16;
let runtime, initial, expected, dataExpected, visits = 0;
runtime = instantiate(fs.readFileSync(process.argv[2]), bytes => {
    const label = Buffer.from(bytes).toString('utf8').trim();
    const memory = runtime.instance.exports.memory, data = runtime.instance.exports.data_memory_1;
    assert.equal(runtime.instance.exports.test_stack_top_0.value, initial + frame,
        'fixed array conversion live frame top differs');
    if (visits++ === 0) {
        assert.equal(label, 'before');
        assert.equal(runtime.instance.exports.test_stack_top_1.value, 1);
        const before = snapshotMemory(memory);
        assert.deepEqual([0, 8, 16, 24].map(n => before.readBigInt64LE(initial + n)), [7n, -8n, 3n, 4n]);
        if (mode === 'grow') new Uint8Array(memory.buffer).fill(0xa5, initial + 32, initial + 48);
        new Uint8Array(memory.buffer).fill(0xa5, initial + frame, initial + frame + 16);
        new Uint8Array(memory.buffer)[initial + frame + 16] = 0x6c;
        expected = snapshotMemory(memory);
        if (mode !== 'stored') {
            expected.writeBigInt64LE(10n, initial + frame); expected.writeBigInt64LE(-4n, initial + frame + 8);
        }
        if (mode === 'grow') {
            expected.writeBigUInt64LE(0x100000001n, initial + 32); expected.writeBigInt64LE(2n, initial + 40);
        }
        new Uint8Array(data.buffer).fill(0x5a, 1); new Uint8Array(data.buffer)[end] = 0xc5;
        dataExpected = snapshotMemory(data);
        if (mode === 'varint') dataExpected[1] = 2;
        else if (prefix) dataExpected.writeUInt32LE(2, 1);
        if (mode === 'limited') dataExpected.writeUInt32LE(2, 5);
        dataExpected.writeBigInt64LE(mode === 'stored' ? 7n : 10n, 1 + prefix);
        dataExpected.writeBigInt64LE(mode === 'stored' ? -8n : -4n, 9 + prefix);
    } else {
        assert.equal(label, 'after');
        assert.equal(runtime.instance.exports.test_stack_top_1.value, end,
            'fixed array conversion live data top differs');
        assert.deepEqual(snapshotMemory(memory), expected, 'fixed array conversion memory 0 image differs');
        assert.deepEqual(snapshotMemory(data), dataExpected, 'fixed array conversion data image differs');
    }
    assert.equal(runtime.pendingPrints, 0); fs.writeSync(1, bytes);
});
initial = runtime.instance.exports.test_stack_top_0.value;
runCompleted(runtime); assert.equal(visits, 2);
assert.equal(runtime.instance.exports.test_stack_top_0.value, initial);
assert.equal(runtime.instance.exports.test_stack_top_1.value, 1);
assert.deepEqual(snapshotMemory(runtime.instance.exports.memory), expected);
assert.deepEqual(snapshotMemory(runtime.instance.exports.data_memory_1), dataExpected);
