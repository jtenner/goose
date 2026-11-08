import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate, GooseFailure } from '../scripts/run_wasm.mjs';
import { snapshotMemory } from './wasm_memory_snapshot.mjs';
const [file, mode, record] = process.argv.slice(2);
assert(['bounds', 'division'].includes(mode));
let runtime, initial, frame, data, visits = 0;
runtime = instantiate(fs.readFileSync(file), bytes => {
    assert.equal(Buffer.from(bytes).toString('utf8'), 'before\n', 'array assignment invalid target ran RHS');
    assert.equal(visits++, 0);
    assert.equal(runtime.instance.exports.test_stack_top_0.value, initial);
    if (mode === 'division') {
        const view = new Uint8Array(runtime.instance.exports.memory.buffer);
        view.fill(0xb6, initial, initial + 16); view[initial + 16] = 0x6c;
    }
    frame = snapshotMemory(runtime.instance.exports.memory);
    if (mode === 'division') {
        assert.equal(frame.readBigInt64LE(8), 0n); assert.equal(frame[16], 3);
        assert.deepEqual([17, 25, 33].map(n => frame.readBigInt64LE(n)), [1n, 2n, 3n]);
    } else {
        assert.equal(runtime.instance.exports.test_stack_top_1.value, 30);
        data = snapshotMemory(runtime.instance.exports.data_memory_1);
        assert.equal(data.readUInt32LE(1), 1); assert.equal(data[5], 3);
        assert.deepEqual([6, 14, 22].map(n => data.readBigInt64LE(n)), [1n, 2n, 3n]);
    }
    assert.equal(runtime.pendingPrints, 0); fs.writeSync(1, bytes);
});
initial = runtime.instance.exports.test_stack_top_0.value;
let failure;
try { runtime.run(); } catch (error) { failure = error; }
if (!(failure instanceof GooseFailure)) { if (failure) throw failure; assert.fail('array assignment did not fail'); }
assert.match(failure.message, mode === 'bounds' ? /array index out of bounds/ : /division by zero/);
assert.equal(visits, 1);
assert.equal(runtime.instance.exports.test_stack_top_0.value, initial + (mode === 'division' ? 16 : 0),
    'array assignment failure reservation differs');
const actual = snapshotMemory(runtime.instance.exports.memory);
// An incomplete RHS has no value contract inside its private reservation.
if (mode === 'division') actual.copy(frame, initial, initial, initial + 16);
assert.deepEqual(actual, frame, 'array assignment protected memory 0 image differs');
if (mode === 'bounds') {
    assert.equal(runtime.instance.exports.test_stack_top_1.value, 30);
    assert.deepEqual(snapshotMemory(runtime.instance.exports.data_memory_1), data,
        'array assignment invalid target changed data image');
}
assert.equal(runtime.pendingPrints, 0); assert.equal(runtime.pendingSnapshots, 0);
assert.throws(() => runtime.run(), error => error instanceof GooseFailure && /only once/.test(error.message));
if (record) fs.writeFileSync(record, JSON.stringify({ target: mode === 'division' ? 17 : null, initial }));
