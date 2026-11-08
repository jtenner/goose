import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';
import { snapshotMemory } from './wasm_memory_snapshot.mjs';
const data = process.argv[3] === 'data';
const pattern = Buffer.alloc(28);
pattern.writeFloatLE(1.25, 0); pattern.writeDoubleLE(45.125, 6);
pattern.writeFloatLE(-2.5, 14); pattern.writeDoubleLE(-37.25, 20);
let runtime, initial, expected, dataExpected, visits = 0;
runtime = instantiate(fs.readFileSync(process.argv[2]), bytes => {
    const label = Buffer.from(bytes).toString('utf8').trim();
    assert.equal(runtime.instance.exports.test_stack_top_0.value, initial + (data ? 0 : 43),
        'adapted negation live frame top differs');
    const memory = runtime.instance.exports.memory;
    if (visits++ === 0) {
        assert.equal(label, 'before');
        const before = snapshotMemory(memory);
        const source = before.subarray(0, initial).indexOf(pattern);
        assert(source >= 0);
        assert.equal(before.subarray(0, initial).indexOf(pattern, source + 1), -1);
        const view = new DataView(memory.buffer);
        view.setUint32(source, 0x7f800123, true);
        view.setBigUint64(source + 6, 0x7ff0000000000456n, true);
        view.setUint32(source + 14, 0x80000000, true);
        view.setBigUint64(source + 20, 0x8000000000000000n, true);
        new Uint8Array(memory.buffer).set([0xc1, 0xc2], source + 4);
        new Uint8Array(memory.buffer).set([0xc3, 0xc4], source + 18);
        if (!data) {
            new Uint8Array(memory.buffer).fill(0xa5, initial, initial + 43);
            new Uint8Array(memory.buffer)[initial + 43] = 0x5a;
        }
        expected = snapshotMemory(memory);
        const write = (target, base) => {
            target[base] = 2;
            target.writeUInt32LE(0xff800123, base + 1);
            target.writeBigUInt64LE(0xfff0000000000456n, base + 7);
            target.writeUInt32LE(0, base + 15);
            target.writeBigUInt64LE(0n, base + 21);
        };
        if (data) {
            assert.equal(runtime.instance.exports.test_stack_top_1.value, 1);
            const owner = runtime.instance.exports.data_memory_1;
            new Uint8Array(owner.buffer).fill(0x5a, 1);
            new Uint8Array(owner.buffer)[48] = 0x3c;
            dataExpected = snapshotMemory(owner);
            dataExpected.writeUInt32LE(1, 1);
            write(dataExpected, 5);
        } else write(expected, initial);
    } else {
        assert.deepEqual(snapshotMemory(memory), expected, 'adapted negation memory 0 image differs');
        if (data) {
            assert.equal(runtime.instance.exports.test_stack_top_1.value, 48,
                'adapted negation live data top differs');
            assert.deepEqual(snapshotMemory(runtime.instance.exports.data_memory_1), dataExpected,
                'adapted negation data memory image differs');
        }
        assert.equal(label, 'after=2,false,false');
    }
    assert.equal(runtime.pendingPrints, 0);
    fs.writeSync(1, bytes);
});
initial = runtime.instance.exports.test_stack_top_0.value;
runCompleted(runtime);
assert.equal(visits, 2);
assert.equal(runtime.instance.exports.test_stack_top_0.value, initial);
assert.deepEqual(snapshotMemory(runtime.instance.exports.memory), expected,
    'adapted negation completed memory 0 image differs');
if (data) {
    assert.equal(runtime.instance.exports.test_stack_top_1.value, 1);
    assert.deepEqual(snapshotMemory(runtime.instance.exports.data_memory_1), dataExpected);
}
