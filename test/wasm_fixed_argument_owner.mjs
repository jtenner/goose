import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';
import { snapshotMemory } from './wasm_memory_snapshot.mjs';
const [file, metadata] = process.argv.slice(2);
const image = Buffer.alloc(9);
image[0] = 90;
image.writeBigInt64LE(72623859790382856n, 1);
const labels = ['arg-live', 'callee-live', 'callee-defer', 'done'];
let runtime, initial, expected, source, visits = 0;
runtime = instantiate(fs.readFileSync(file), bytes => {
    const label = Buffer.from(bytes).toString('utf8').trim();
    assert.equal(label, labels[visits++]);
    const top = initial + (label === 'arg-live' ? 9 : label === 'done' ? 0 : 18);
    assert.equal(runtime.instance.exports.test_stack_top_0.value, top,
        'fixed argument live frame top differs');
    const memory = runtime.instance.exports.memory;
    if (label === 'arg-live') {
        const before = snapshotMemory(memory);
        source = before.subarray(0, initial).indexOf(image);
        assert(source >= 0);
        assert.equal(before.subarray(0, initial).indexOf(image, source + 1), -1);
        assert.deepEqual(before.subarray(initial, initial + 9), image,
            'fixed argument snapshot image differs');
        new Uint8Array(memory.buffer)[initial + 18] = 165;
        expected = snapshotMemory(memory);
        expected.writeBigInt64LE(12n, source + 1);
        image.copy(expected, initial + 9);
    } else {
        if (label === 'callee-defer') expected.writeBigInt64LE(9n, initial + 10);
        assert.deepEqual(snapshotMemory(memory), expected,
            'fixed argument callee image differs');
    }
    assert.equal(runtime.pendingPrints, 0);
    fs.writeSync(1, bytes);
});
initial = runtime.instance.exports.test_stack_top_0.value;
runCompleted(runtime);
assert.equal(visits, 4);
assert.equal(runtime.instance.exports.test_stack_top_0.value, initial,
    'fixed argument frame top was not restored');
assert.deepEqual(snapshotMemory(runtime.instance.exports.memory), expected,
    'fixed argument completed image differs');
if (metadata) fs.writeFileSync(metadata, JSON.stringify({ source, initial }) + '\n');
