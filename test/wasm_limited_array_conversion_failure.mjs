import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate, GooseFailure } from '../scripts/run_wasm.mjs';
import { snapshotMemory } from './wasm_memory_snapshot.mjs';
const count = Number(process.argv[3]); assert([256, 65536].includes(count));
const width = count === 256 ? 2 : 4, frame = count + width;
let runtime, initial, expected, data, visits = 0;
runtime = instantiate(fs.readFileSync(process.argv[2]), bytes => {
    assert.equal(Buffer.from(bytes).toString('utf8'), 'before\n', 'prefix range executed after failed conversion');
    assert.equal(visits++, 0);
    const e = runtime.instance.exports;
    assert.equal(e.test_stack_top_0.value, initial + frame, 'prefix range live frame top differs');
    assert.equal(e.test_stack_top_1.value, 1, 'prefix range allocated receiver before check');
    const view = new Uint8Array(e.memory.buffer); view[initial + frame] = 0x6c;
    expected = snapshotMemory(e.memory);
    assert.equal(width === 2 ? expected.readUInt16LE(initial) : expected.readUInt32LE(initial), count);
    assert.deepEqual([...expected.subarray(initial + width, initial + frame)], Array.from({length: count}, (_, i) => i & 255));
    new Uint8Array(e.data_memory_1.buffer).fill(0x5a, 1); data = snapshotMemory(e.data_memory_1);
    assert.equal(runtime.pendingPrints, 0); fs.writeSync(1, bytes);
});
initial = runtime.instance.exports.test_stack_top_0.value;
let failure; try { runtime.run(); } catch (error) { failure = error; }
if (!(failure instanceof GooseFailure)) { if (failure) throw failure; assert.fail('prefix range did not fail'); }
assert.match(failure.message, /^goose runtime error: array length exceeds stored prefix(?: at |$)/);
assert.equal(visits, 1);
const e = runtime.instance.exports;
// A failed activation is consumed. Its frame is retained; no receiver was allocated.
assert.equal(e.test_stack_top_0.value, initial + frame, 'prefix range failed frame state differs');
assert.equal(e.test_stack_top_1.value, 1, 'prefix range allocated receiver before check');
assert.deepEqual(snapshotMemory(e.memory), expected, 'prefix range protected memory 0 differs');
assert.deepEqual(snapshotMemory(e.data_memory_1), data, 'prefix range protected data memory differs');
assert.equal(runtime.pendingPrints, 0); assert.equal(runtime.pendingSnapshots, 0);
assert.throws(() => runtime.run(), error => error instanceof GooseFailure && /only once/.test(error.message));
