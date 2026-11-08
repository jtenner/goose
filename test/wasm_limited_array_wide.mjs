import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';
import { snapshotMemory } from './wasm_memory_snapshot.mjs';
let runtime, initial, expected, visits = 0;
runtime = instantiate(fs.readFileSync(process.argv[2]), bytes => {
    const label = Buffer.from(bytes).toString('utf8').trim();
    assert.equal(runtime.instance.exports.test_stack_top_0.value, initial + 66312, 'limited wide live frame top differs');
    if (label === 'before') {
        assert.equal(visits++, 0);
        const view = new Uint8Array(runtime.instance.exports.memory.buffer);
        view.fill(0xa5, initial + 258, initial + 66312); view[initial + 66312] = 0x6c;
        expected = snapshotMemory(runtime.instance.exports.memory); assert.equal(expected.readUInt16LE(initial), 256);
        expected.writeUInt32LE(256, initial + 258);
        expected.copy(expected, initial + 262, initial + 2, initial + 258);
    } else {
        assert.equal(label, visits++ === 1 ? 'wide' : 'after');
        if (label === 'after') {
            expected.writeUInt16LE(256, initial + 65798);
            expected.copy(expected, initial + 65800, initial + 262, initial + 518);
        }
        assert.deepEqual(snapshotMemory(runtime.instance.exports.memory), expected, 'limited wide memory 0 image differs');
    }
    assert.equal(runtime.pendingPrints, 0); fs.writeSync(1, bytes);
});
initial = runtime.instance.exports.test_stack_top_0.value;
runCompleted(runtime); assert.equal(visits, 3);
assert.equal(runtime.instance.exports.test_stack_top_0.value, initial, 'limited wide completed frame top differs');
assert.deepEqual(snapshotMemory(runtime.instance.exports.memory), expected);
