import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';
import { snapshotMemory } from './wasm_memory_snapshot.mjs';
const mode = process.argv[3];
assert(['stored', 'call'].includes(mode));
let runtime, initial, expected, visits = 0;
runtime = instantiate(fs.readFileSync(process.argv[2]), bytes => {
    const label = Buffer.from(bytes).toString('utf8').trim();
    assert.equal(runtime.instance.exports.test_stack_top_0.value, initial + 41,
        'limited conversion live frame top differs');
    const memory = runtime.instance.exports.memory;
    if (label === 'before') {
        assert.equal(visits++, 0);
        const view = new Uint8Array(memory.buffer);
        view.fill(0xa5, initial + 16, initial + 41);
        view.fill(0xc7, initial + 16, initial + 33);
        view.fill(0xb6, initial + 41, initial + 57); view[initial + 57] = 0x6c;
        expected = snapshotMemory(memory);
        assert.equal(expected.readBigInt64LE(initial), 7n);
        assert.equal(expected.readBigInt64LE(initial + 8), -8n);
        expected[initial + 16] = 2;
        expected.writeBigInt64LE(7n, initial + 17);
        expected.writeBigInt64LE(-8n, initial + 25);
        if (mode === 'call') {
            expected.writeBigInt64LE(7n, initial + 41);
            expected.writeBigInt64LE(-8n, initial + 49);
        }
    } else {
        assert.equal(label, 'after'); assert.equal(visits++, 1);
        assert.deepEqual(snapshotMemory(memory), expected, 'limited conversion memory 0 image differs');
    }
    assert.equal(runtime.pendingPrints, 0); fs.writeSync(1, bytes);
});
initial = runtime.instance.exports.test_stack_top_0.value;
runCompleted(runtime); assert.equal(visits, 2);
assert.equal(runtime.instance.exports.test_stack_top_0.value, initial,
    'limited conversion completed frame top differs');
assert.deepEqual(snapshotMemory(runtime.instance.exports.memory), expected, 'limited conversion completed image differs');
