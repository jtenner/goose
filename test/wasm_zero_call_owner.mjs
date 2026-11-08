import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';
import { snapshotMemory } from './wasm_memory_snapshot.mjs';
let runtime, initial, expected, visits = 0;
runtime = instantiate(fs.readFileSync(process.argv[2]), bytes => {
    const label = Buffer.from(bytes).toString('utf8').trim();
    const memory = runtime.instance.exports.memory;
    if (visits === 0) {
        assert.equal(label, 'before');
        assert.equal(runtime.instance.exports.test_stack_top_0.value, initial + 2,
            'zero call caller owner top differs');
        new Uint8Array(memory.buffer).set([0xa1, 0xa2, 0xa3, 0xa4, 0xc5], initial);
        expected = snapshotMemory(memory);
    } else {
        assert.equal(label, visits === 1 ? 'inside' : 'after');
        assert.equal(runtime.instance.exports.test_stack_top_0.value, initial + (visits === 1 ? 4 : 2),
            'zero call live owner top differs');
        const actual = snapshotMemory(memory);
        // These are the result, caller argument and callee parameter's
        // identity reservations. They have no payload value contract.
        // Source identity and every byte outside those three owners are exact.
        actual.copy(expected, initial + 1, initial + 1, initial + 4);
        assert.deepEqual(actual, expected, 'zero call memory 0 image differs');
    }
    visits++; assert.equal(runtime.pendingPrints, 0); fs.writeSync(1, bytes);
});
initial = runtime.instance.exports.test_stack_top_0.value;
runCompleted(runtime); assert.equal(visits, 3);
assert.equal(runtime.instance.exports.test_stack_top_0.value, initial);
assert.deepEqual(snapshotMemory(runtime.instance.exports.memory), expected);
