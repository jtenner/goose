import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';
import { snapshotMemory } from './wasm_memory_snapshot.mjs';
const mode = process.argv[3];
const plans = {
    grow_variable: ['grow', 'u16', 3, 3],
    grow_runtime: ['grow', 'runtime', 3, 3],
    runtime_variable: ['runtime', 'u16', 3, 5],
    runtime_grow: ['runtime', 'grow', 3, 5],
    grow_empty: ['grow', 'u16', 0, 0],
    runtime_empty: ['runtime', 'u16', 0, 5],
    grow_leb128: ['grow', 'leb', 128, 128],
};
assert(mode in plans);
const [sourceKind, targetKind, count, capacity] = plans[mode];
const sourcePrefix = sourceKind === 'grow' ? 0 : 8;
const targetPrefix = targetKind === 'grow' ? 0 : targetKind === 'runtime' ? 8 : 2;
const payload = count * 8;
const sourceTop = 1 + sourcePrefix + capacity * 8;
const targetTop = 1 + targetPrefix + payload;
const frameBytes = 16 * (Number(sourceKind === 'grow') + Number(targetKind === 'grow'));
let runtime, initial, frame, source, target, visits = 0;
runtime = instantiate(fs.readFileSync(process.argv[2]), bytes => {
    const label = Buffer.from(bytes).toString('utf8').trim();
    const e = runtime.instance.exports;
    assert.equal(e.test_stack_top_0.value, initial + frameBytes, 'nonfixed live frame top differs');
    assert.equal(e.test_stack_top_1.value, sourceTop, 'nonfixed source top differs');
    if (label === 'before') {
        assert.equal(visits++, 0);
        assert.equal(e.test_stack_top_2.value, 1, 'nonfixed receiver allocated before checkpoint');
        for (const memory of [e.data_memory_1, e.data_memory_2])
            if (memory.buffer.byteLength === 0) memory.grow(1);
        const mv = new Uint8Array(e.memory.buffer);
        mv[initial + frameBytes + 16] = 108;
        if (targetKind === 'grow') mv.fill(182, initial, initial + 16);
        frame = snapshotMemory(e.memory);
        if (sourceKind === 'grow') {
            assert.equal(frame.readBigUInt64LE(initial), (1n << 32n) | 1n);
            assert.equal(frame.readBigUInt64LE(initial + 8), BigInt(count));
        }
        if (targetKind === 'grow') {
            frame.writeBigUInt64LE((2n << 32n) | 1n, initial);
            frame.writeBigUInt64LE(BigInt(count), initial + 8);
        }
        const sv = new Uint8Array(e.data_memory_1.buffer);
        sv.fill(199, 1 + sourcePrefix + payload, sourceTop);
        sv.fill(212, sourceTop);
        source = snapshotMemory(e.data_memory_1);
        if (sourceKind === 'runtime') {
            assert.equal(source.readUInt32LE(1), capacity);
            assert.equal(source.readUInt32LE(5), count);
        }
        for (let i = 0; i < count; i++)
            assert.equal(source.readBigInt64LE(1 + sourcePrefix + i * 8),
                count === 128 ? 7n : [7n, -8n, 900n][i]);
        const tv = new Uint8Array(e.data_memory_2.buffer);
        tv.fill(165, 1); tv[targetTop] = 108;
        target = snapshotMemory(e.data_memory_2);
        if (targetKind === 'u16') target.writeUInt16LE(count, 1);
        else if (targetKind === 'runtime') {
            target.writeUInt32LE(count, 1); target.writeUInt32LE(count, 5);
        } else if (targetKind === 'leb') { target[1] = 128; target[2] = 1; }
        source.copy(target, 1 + targetPrefix, 1 + sourcePrefix, 1 + sourcePrefix + payload);
    } else {
        assert.equal(label, 'after'); assert.equal(visits++, 1);
        assert.equal(e.test_stack_top_2.value, targetTop, 'nonfixed receiver top differs');
        assert.deepEqual(snapshotMemory(e.memory), frame, 'nonfixed memory 0 image differs');
        assert.deepEqual(snapshotMemory(e.data_memory_1), source, 'nonfixed source image differs');
        assert.deepEqual(snapshotMemory(e.data_memory_2), target, 'nonfixed receiver image differs');
    }
    assert.equal(runtime.pendingPrints, 0); fs.writeSync(1, bytes);
});
initial = runtime.instance.exports.test_stack_top_0.value;
runCompleted(runtime); assert.equal(visits, 2);
const e = runtime.instance.exports;
assert.equal(e.test_stack_top_0.value, initial, 'nonfixed completed frame top differs');
assert.equal(e.test_stack_top_1.value, 1, 'nonfixed completed source top differs');
assert.equal(e.test_stack_top_2.value, 1, 'nonfixed completed receiver top differs');
assert.deepEqual(snapshotMemory(e.memory), frame, 'nonfixed completed memory 0 image differs');
assert.deepEqual(snapshotMemory(e.data_memory_1), source, 'nonfixed completed source image differs');
assert.deepEqual(snapshotMemory(e.data_memory_2), target, 'nonfixed completed receiver image differs');
if (process.argv[4]) fs.writeFileSync(process.argv[4], JSON.stringify({initial, frameBytes, sourceTop, targetTop}));
