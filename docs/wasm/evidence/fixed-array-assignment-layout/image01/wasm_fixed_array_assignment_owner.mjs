import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';
import { snapshotMemory } from './wasm_memory_snapshot.mjs';
const mode = process.argv[3]; assert(['stored', 'call', 'zero'].includes(mode));
const frame = mode === 'stored' ? 41 : 25, header = mode === 'stored' ? 16 : 0;
const scratch = mode === 'zero' ? 1 : 16;
let runtime, initial, before, expected, visits = 0;
const checkImage = (wanted, reason) => {
    const actual = snapshotMemory(runtime.instance.exports.memory);
    if (mode === 'zero') wanted[initial + frame] = actual[initial + frame];
    assert.deepEqual(actual, wanted, reason);
};
runtime = instantiate(fs.readFileSync(process.argv[2]), bytes => {
    const label = Buffer.from(bytes).toString('utf8').trim();
    assert.equal(runtime.instance.exports.test_stack_top_0.value,
        initial + frame + (label === 'inside' ? 1 : 0), 'array assignment live frame top differs');
    if (label === 'before') {
        assert.equal(visits++, 0);
        const view = new Uint8Array(runtime.instance.exports.memory.buffer);
        view.fill(0xb6, initial + frame, initial + frame + scratch);
        view[initial + frame + scratch] = 0x6c;
        before = snapshotMemory(runtime.instance.exports.memory);
        assert.equal(before[initial + header], 3);
        assert.deepEqual([1, 9, 17].map(n => before.readBigInt64LE(initial + header + n)), [1n, 2n, 3n]);
        if (mode === 'stored') assert.deepEqual([0, 8].map(n => before.readBigInt64LE(initial + n)), [7n, -8n]);
        expected = Buffer.from(before); expected[initial + header] = mode === 'zero' ? 0 : 2;
        if (mode !== 'zero') {
            expected.writeBigInt64LE(7n, initial + header + 1);
            expected.writeBigInt64LE(-8n, initial + header + 9);
        }
        if (mode === 'call') {
            expected.writeBigInt64LE(7n, initial + frame);
            expected.writeBigInt64LE(-8n, initial + frame + 8);
        }
    } else if (label === 'inside') {
        assert.equal(mode, 'zero'); assert.equal(visits++, 1);
        checkImage(before, 'array assignment source effects changed target early');
    } else {
        assert.equal(label, 'after'); assert.equal(visits++, mode === 'zero' ? 2 : 1);
        checkImage(expected, 'array assignment memory 0 image differs');
    }
    assert.equal(runtime.pendingPrints, 0); fs.writeSync(1, bytes);
});
initial = runtime.instance.exports.test_stack_top_0.value;
runCompleted(runtime); assert.equal(visits, mode === 'zero' ? 3 : 2);
assert.equal(runtime.instance.exports.test_stack_top_0.value, initial, 'array assignment completed frame top differs');
checkImage(expected, 'array assignment completed image differs');
