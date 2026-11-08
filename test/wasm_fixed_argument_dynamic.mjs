import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';
const [file] = process.argv.slice(2);
let runtime, initial, firstBase, secondBase, visits = 0;
runtime = instantiate(fs.readFileSync(file), bytes => {
    const label = Buffer.from(bytes).toString('utf8').trim();
    const inside = label === 'inside';
    assert.equal(label, visits < 2 ? 'inside' : 'dynamic_base');
    assert.equal(runtime.instance.exports.test_stack_top_0.value, initial + (inside ? 24 : 8),
        'fixed argument dynamic frame top differs');
    if (inside) {
        assert.equal(runtime.instance.exports.test_stack_top_1.value, firstBase + 12,
            'fixed argument dynamic memory base differs');
        assert.equal(runtime.instance.exports.test_stack_top_2.value, secondBase + (visits === 0 ? 0 : 12),
            'fixed argument dynamic memory base differs');
        const first = Buffer.from(new Uint8Array(runtime.instance.exports.data_memory_1.buffer));
        const second = Buffer.from(new Uint8Array(runtime.instance.exports.data_memory_2.buffer));
        assert.equal(first.readUInt32LE(firstBase), 1);
        assert.equal(first.readBigInt64LE(firstBase + 4), visits === 0 ? 1n : 9n,
            'fixed argument dynamic memory base differs');
        assert.equal(second.readBigInt64LE(secondBase + 4), visits === 0 ? 0n : 1n,
            'fixed argument dynamic memory base differs');
        if (visits === 1) assert.equal(second.readUInt32LE(secondBase), 1);
    } else {
        assert.equal(runtime.instance.exports.test_stack_top_1.value, firstBase);
        assert.equal(runtime.instance.exports.test_stack_top_2.value, secondBase);
    }
    visits++;
    fs.writeSync(1, bytes);
});
initial = runtime.instance.exports.test_stack_top_0.value;
firstBase = runtime.instance.exports.test_stack_top_1.value;
secondBase = runtime.instance.exports.test_stack_top_2.value;
runCompleted(runtime);
assert.equal(visits, 3);
assert.equal(runtime.instance.exports.test_stack_top_0.value, initial);
assert.equal(runtime.instance.exports.test_stack_top_1.value, firstBase);
assert.equal(runtime.instance.exports.test_stack_top_2.value, secondBase);
