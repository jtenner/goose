import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';
import { snapshotMemory } from './wasm_memory_snapshot.mjs';
const data = process.argv[3] === 'data';
const mode = process.argv[4] ?? 'finite';
assert(['finite', 'bits', 'nan'].includes(mode));
const pattern = (a, b) => { const x = Buffer.alloc(14); x.writeFloatLE(a); x.writeDoubleLE(b, 6); return x; };
let runtime, initial, top, expected, dataExpected, visits = 0, target;
runtime = instantiate(fs.readFileSync(process.argv[2]), bytes => {
    const label = Buffer.from(bytes).toString('utf8').trim();
    const memory = runtime.instance.exports.memory;
    if (visits++ === 0) {
        assert.equal(label, 'before');
        top = runtime.instance.exports.test_stack_top_0.value;
        const before = snapshotMemory(memory);
        const left = before.subarray(0, initial).indexOf(pattern(1.25, 45.125));
        const right = before.subarray(0, initial).indexOf(pattern(-2.5, -37.25));
        assert(left >= 0 && right >= 0 && left !== right);
        assert.equal(before.subarray(0, initial).indexOf(pattern(1.25, 45.125), left + 1), -1);
        assert.equal(before.subarray(0, initial).indexOf(pattern(-2.5, -37.25), right + 1), -1);
        target = data ? 5 : left;
        const targetMemory = data ? runtime.instance.exports.data_memory_1 : memory;
        if (data) {
            assert.equal(runtime.instance.exports.test_stack_top_1.value, 19);
            assert.deepEqual(snapshotMemory(targetMemory).subarray(5, 19), pattern(1.25, 45.125));
            new Uint8Array(targetMemory.buffer)[19] = 0x3c;
        }
        const view = new DataView(targetMemory.buffer), rhs = new DataView(memory.buffer);
        if (mode === 'bits') {
            view.setUint32(target, 0x80000000, true); rhs.setUint32(right, 0x80000000, true);
            view.setBigUint64(target + 6, 0x7ff0000000000000n, true);
        } else if (mode === 'nan') {
            view.setUint32(target, 0x7f800123, true);
            view.setBigUint64(target + 6, 0x7ff0000000000456n, true);
        }
        new Uint8Array(targetMemory.buffer).set([0xc1, 0xc2], target + 4);
        new Uint8Array(memory.buffer).set([0xd1, 0xd2], right + 4);
        expected = snapshotMemory(memory);
        if (data) dataExpected = snapshotMemory(targetMemory);
        const image = data ? dataExpected : expected;
        if (mode === 'finite') { image.writeFloatLE(-1.25, target); image.writeDoubleLE(7.875, target + 6); }
        else if (mode === 'bits') {
            image.writeUInt32LE(0x80000000, target); image.writeBigUInt64LE(0x7ff0000000000000n, target + 6);
        }
    } else {
        assert.equal(runtime.instance.exports.test_stack_top_0.value, top, 'compound live frame top differs');
        if (mode === 'nan') {
            const actual = snapshotMemory(data ? runtime.instance.exports.data_memory_1 : memory);
            const image = data ? dataExpected : expected;
            const f32 = actual.readUInt32LE(target), f64 = actual.readBigUInt64LE(target + 6);
            assert.equal(f32 & 0x7fc00000, 0x7fc00000);
            assert.equal(f64 & 0x7ff8000000000000n, 0x7ff8000000000000n);
            image.writeUInt32LE(f32, target); image.writeBigUInt64LE(f64, target + 6);
        }
        assert.deepEqual(snapshotMemory(memory), expected, 'compound memory 0 image differs');
        if (data) {
            assert.equal(runtime.instance.exports.test_stack_top_1.value, 19);
            assert.deepEqual(snapshotMemory(runtime.instance.exports.data_memory_1), dataExpected,
                'compound data memory image differs');
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
