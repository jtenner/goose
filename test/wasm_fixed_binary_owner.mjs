import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';
import { snapshotMemory } from './wasm_memory_snapshot.mjs';
const data = process.argv[3] === 'data';
const mode = process.argv[4] ?? 'finite';
assert(['finite', 'bits', 'nan'].includes(mode));
const leftPattern = Buffer.alloc(14), rightPattern = Buffer.alloc(14);
leftPattern.writeFloatLE(1.25); leftPattern.writeDoubleLE(45.125, 6);
rightPattern.writeFloatLE(-2.5); rightPattern.writeDoubleLE(-37.25, 6);
let runtime, initial, expected, dataExpected, visits = 0;
runtime = instantiate(fs.readFileSync(process.argv[2]), bytes => {
    const label = Buffer.from(bytes).toString('utf8').trim();
    assert.equal(runtime.instance.exports.test_stack_top_0.value, initial + (data ? 0 : 14),
        'fixed binary live frame top differs');
    const memory = runtime.instance.exports.memory;
    if (visits++ === 0) {
        assert.equal(label, 'before');
        const before = snapshotMemory(memory);
        const left = before.subarray(0, initial).indexOf(leftPattern);
        const right = before.subarray(0, initial).indexOf(rightPattern);
        assert(left >= 0 && right >= 0 && left !== right);
        assert.equal(before.subarray(0, initial).indexOf(leftPattern, left + 1), -1);
        assert.equal(before.subarray(0, initial).indexOf(rightPattern, right + 1), -1);
        const view = new DataView(memory.buffer);
        if (mode === 'bits') {
            view.setUint32(left, 0x80000000, true);
            view.setUint32(right, 0x80000000, true);
            view.setBigUint64(left + 6, 0x7ff0000000000000n, true);
        } else if (mode === 'nan') {
            view.setUint32(left, 0x7f800123, true);
            view.setBigUint64(left + 6, 0x7ff0000000000456n, true);
        }
        new Uint8Array(memory.buffer).set([0xc1, 0xc2], left + 4);
        new Uint8Array(memory.buffer).set([0xd1, 0xd2], right + 4);
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
        }
        const target = data ? dataExpected : expected, base = data ? 5 : initial;
        if (mode === 'finite') {
            target.writeFloatLE(-1.25, base); target.writeDoubleLE(7.875, base + 6);
        } else if (mode === 'bits') {
            target.writeUInt32LE(0x80000000, base);
            target.writeBigUInt64LE(0x7ff0000000000000n, base + 6);
        }
    } else {
        if (mode === 'nan') {
            const image = snapshotMemory(data ? runtime.instance.exports.data_memory_1 : memory);
            const target = data ? dataExpected : expected, base = data ? 5 : initial;
            const f32 = image.readUInt32LE(base), f64 = image.readBigUInt64LE(base + 6);
            // Arithmetic NaN payloads may vary. Both results must be quiet
            // NaNs; every other byte, including source payloads, is exact.
            assert.equal(f32 & 0x7fc00000, 0x7fc00000, 'fixed binary f32 result is not a quiet NaN');
            assert.equal(f64 & 0x7ff8000000000000n, 0x7ff8000000000000n,
                'fixed binary f64 result is not a quiet NaN');
            target.writeUInt32LE(f32, base); target.writeBigUInt64LE(f64, base + 6);
        }
        assert.deepEqual(snapshotMemory(memory), expected, 'fixed binary memory 0 image differs');
        if (data) {
            assert.equal(runtime.instance.exports.test_stack_top_1.value, 19);
            assert.deepEqual(snapshotMemory(runtime.instance.exports.data_memory_1), dataExpected,
                'fixed binary data memory image differs');
        }
        assert.equal(label, mode === 'nan' ? 'after=false,false' : 'after=true,true');
    }
    assert.equal(runtime.pendingPrints, 0);
    fs.writeSync(1, bytes);
});
initial = runtime.instance.exports.test_stack_top_0.value;
runCompleted(runtime);
assert.equal(visits, 2);
assert.equal(runtime.instance.exports.test_stack_top_0.value, initial);
assert.deepEqual(snapshotMemory(runtime.instance.exports.memory), expected);
if (data) {
    assert.equal(runtime.instance.exports.test_stack_top_1.value, 1);
    assert.deepEqual(snapshotMemory(runtime.instance.exports.data_memory_1), dataExpected);
}
