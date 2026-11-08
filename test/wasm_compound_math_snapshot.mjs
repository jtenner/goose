import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';
import { snapshotMemory } from './wasm_memory_snapshot.mjs';
const pattern = Buffer.alloc(16); pattern.writeBigInt64LE(7n); pattern.writeBigInt64LE(-8n, 8);
let runtime, initial, expected, source, visits = 0;
runtime = instantiate(fs.readFileSync(process.argv[2]), bytes => {
    const label = Buffer.from(bytes).toString('utf8').trim(), memory = runtime.instance.exports.memory;
    if (visits === 0) {
        assert.equal(label, 'before');
        assert.equal(runtime.instance.exports.test_stack_top_0.value, initial);
        const before = snapshotMemory(memory); source = before.subarray(0, initial).indexOf(pattern);
        assert(source >= 0);
        assert.equal(before.subarray(0, initial).indexOf(pattern, source + 1), -1);
        new Uint8Array(memory.buffer).fill(0xa5, initial, initial + 32);
        new Uint8Array(memory.buffer)[initial + 32] = 0x6c;
        expected = snapshotMemory(memory);
    } else if (visits === 1) {
        assert.equal(label, 'right');
        assert.equal(runtime.instance.exports.test_stack_top_0.value, initial + 32,
            'compound snapshot RHS top differs');
        expected.writeBigInt64LE(99n, source); expected.writeBigInt64LE(1n, source + 16);
        expected.writeBigInt64LE(7n, initial); expected.writeBigInt64LE(-8n, initial + 8);
        assert.deepEqual(snapshotMemory(memory), expected, 'compound pre-RHS snapshot image differs');
    } else {
        assert.equal(runtime.instance.exports.test_stack_top_0.value, initial,
            'compound snapshot completed top differs');
        expected.writeBigInt64LE(10n, source); expected.writeBigInt64LE(-4n, source + 8);
        expected.writeBigInt64LE(3n, initial + 16); expected.writeBigInt64LE(4n, initial + 24);
        assert.deepEqual(snapshotMemory(memory), expected, 'compound snapshot result image differs');
        assert.equal(label, 'after=10,-4,1');
    }
    visits++; assert.equal(runtime.pendingPrints, 0); fs.writeSync(1, bytes);
});
initial = runtime.instance.exports.test_stack_top_0.value;
runCompleted(runtime); assert.equal(visits, 3);
assert.equal(runtime.instance.exports.test_stack_top_0.value, initial);
assert.deepEqual(snapshotMemory(runtime.instance.exports.memory), expected);
