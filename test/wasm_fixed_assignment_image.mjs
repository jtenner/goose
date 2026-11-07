import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';
import { snapshotMemory } from './wasm_memory_snapshot.mjs';
const [file] = process.argv.slice(2);
const big = Buffer.alloc(9); big.writeBigInt64LE(1000n, 1);
const small = Buffer.alloc(9); small[0] = 1; small[1] = 7;
const empty = Buffer.alloc(9); empty[0] = 2;
let runtime, initial, expected, count = 0;
runtime = instantiate(fs.readFileSync(file), bytes => {
    const text = Buffer.from(bytes).toString('utf8').trim();
    assert.equal(runtime.instance.exports.test_stack_top_0.value, initial + 27);
    if (expected.length !== runtime.instance.exports.memory.buffer.byteLength) {
        const larger = Buffer.alloc(runtime.instance.exports.memory.buffer.byteLength);
        expected.copy(larger); expected = larger;
    }
    if (text === 'seed') {
        assert.equal(count, 0);
        Buffer.concat([big, small, empty]).copy(expected, initial);
        assert.deepEqual(Buffer.from(runtime.instance.exports.memory.buffer), expected,
            'fixed assignment constructors differ from their complete image');
        small.fill(199, 2);
        new Uint8Array(runtime.instance.exports.memory.buffer).set(small, initial + 9);
        small.copy(expected, initial + 9);
    } else if (text === 'copied') {
        assert.equal(count, 1); small.copy(expected, initial);
    } else {
        assert.equal(text, 'emptied'); assert.equal(count, 2); empty.copy(expected, initial + 9);
    }
    assert.deepEqual(Buffer.from(runtime.instance.exports.memory.buffer), expected,
        'exact fixed assignment image differs');
    assert.equal(runtime.pendingPrints, 0);
    count++; fs.writeSync(1, bytes);
});
initial = runtime.instance.exports.test_stack_top_0.value;
expected = snapshotMemory(runtime.instance.exports.memory);
runCompleted(runtime);
assert.equal(count, 3);
assert.equal(runtime.instance.exports.test_stack_top_0.value, initial);
assert.deepEqual(Buffer.from(runtime.instance.exports.memory.buffer), expected,
    'completed fixed assignment image differs');
