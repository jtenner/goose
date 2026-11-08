import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';
import { snapshotMemory } from './wasm_memory_snapshot.mjs';
const data = process.argv[3] === 'data';
const pattern = Buffer.alloc(14); pattern.writeFloatLE(1.25); pattern.writeDoubleLE(45.125, 6);
let runtime, initial, expected, dataExpected, source, visits = 0;
runtime = instantiate(fs.readFileSync(process.argv[2]), bytes => {
    const label = Buffer.from(bytes).toString('utf8').trim();
    assert.equal(runtime.instance.exports.test_stack_top_0.value, initial + (data ? 0 : 14),
        'fixed negation live frame top differs');
    const memory = runtime.instance.exports.memory;
    if (visits++ === 0) {
        assert.equal(label, 'before');
        const before = snapshotMemory(memory);
        source = before.subarray(0, initial).indexOf(pattern); assert(source >= 0);
        assert.equal(before.subarray(0, initial).indexOf(pattern, source + 1), -1);
        const target = new DataView(memory.buffer);
        target.setUint32(source, 0x7f800123, true);
        target.setBigUint64(source + 6, 0x7ff0000000000456n, true);
        new Uint8Array(memory.buffer).set([0xc1, 0xc2], source + 4);
        if (!data) {
            new Uint8Array(memory.buffer).fill(0xa5, initial, initial + 14);
            new Uint8Array(memory.buffer)[initial + 14] = 0x5a;
        }
        expected = snapshotMemory(memory);
        if (data) {
            assert.equal(runtime.instance.exports.test_stack_top_1.value, 1);
            const owner = runtime.instance.exports.data_memory_1;
            new Uint8Array(owner.buffer).fill(0x5a, 1);
            new Uint8Array(owner.buffer)[19] = 0x3c;
            dataExpected = snapshotMemory(owner);
            dataExpected.writeUInt32LE(1, 1);
            dataExpected.writeUInt32LE(0xff800123, 5);
            dataExpected.writeBigUInt64LE(0xfff0000000000456n, 11);
        } else {
            expected.writeUInt32LE(0xff800123, initial);
            expected.writeBigUInt64LE(0xfff0000000000456n, initial + 6);
        }
    } else {
        assert(label.startsWith('after='));
        assert.deepEqual(snapshotMemory(memory), expected, 'fixed negation memory 0 image differs');
        if (data) {
            assert.equal(runtime.instance.exports.test_stack_top_1.value, 19,
                'fixed negation live data top differs');
            assert.deepEqual(snapshotMemory(runtime.instance.exports.data_memory_1), dataExpected,
                'fixed negation data memory image differs');
        }
        assert.equal(label, 'after=false,false');
    }
    assert.equal(runtime.pendingPrints, 0);
    fs.writeSync(1, bytes);
});
initial = runtime.instance.exports.test_stack_top_0.value;
runCompleted(runtime);
assert.equal(visits, 2);
assert.equal(runtime.instance.exports.test_stack_top_0.value, initial,
    'fixed negation completed frame top differs');
assert.deepEqual(snapshotMemory(runtime.instance.exports.memory), expected,
    'fixed negation completed memory 0 image differs');
if (data) {
    assert.equal(runtime.instance.exports.test_stack_top_1.value, 1);
    assert.deepEqual(snapshotMemory(runtime.instance.exports.data_memory_1), dataExpected);
}
