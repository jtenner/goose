import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate, GooseFailure } from '../scripts/run_wasm.mjs';
import { snapshotMemory } from './wasm_memory_snapshot.mjs';
let runtime, initial, expected, visits = 0;
runtime = instantiate(fs.readFileSync(process.argv[2]), bytes => {
    const label = Buffer.from(bytes).toString('utf8').trim();
    assert.equal(label, visits === 0 ? 'before' : 'rhs', 'limited capacity executed after failed conversion');
    assert(visits++ < 2);
    const image = snapshotMemory(runtime.instance.exports.memory);
    assert.equal(image[16], 3); assert.deepEqual([...image.subarray(17, 20)], label === 'before' ? [1, 2, 3] : [1, 2, 99]);
    assert.equal(image.readBigInt64LE(8), label === 'before' ? 0n : 1n);
    if (label === 'before') expected = image;
    else { expected.writeBigInt64LE(1n, 8); expected[19] = 99; }
    assert.equal(runtime.pendingPrints, 0); fs.writeSync(1, bytes);
});
initial = runtime.instance.exports.test_stack_top_0.value;
let failure; try { runtime.run(); } catch (error) { failure = error; }
if (!(failure instanceof GooseFailure)) { if (failure) throw failure; assert.fail('limited capacity did not fail'); }
assert.match(failure.message, /capacity/, 'limited capacity wrong failure'); assert.equal(visits, 2);
assert.equal(runtime.instance.exports.test_stack_top_0.value, initial + 258, 'limited capacity source reservation differs');
const actual = snapshotMemory(runtime.instance.exports.memory);
assert.equal(actual.readUInt16LE(initial), 4); assert.deepEqual([...actual.subarray(initial + 2, initial + 6)], [7, 8, 9, 10]);
// Terminal failure consumes the instance. Private result bytes have no published-value contract.
actual.copy(expected, initial, initial, initial + 258);
assert.deepEqual(actual, expected, 'limited capacity published memory image differs');
assert.equal(runtime.pendingPrints, 0); assert.equal(runtime.pendingSnapshots, 0);
assert.throws(() => runtime.run(), error => error instanceof GooseFailure && /only once/.test(error.message));
