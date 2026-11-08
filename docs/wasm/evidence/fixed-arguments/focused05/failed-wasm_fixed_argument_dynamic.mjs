import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';
const [file] = process.argv.slice(2);
let runtime, initial, visits = 0;
runtime = instantiate(fs.readFileSync(file), bytes => {
    const label = Buffer.from(bytes).toString('utf8').trim();
    const inside = label === 'inside';
    assert.equal(label, visits < 2 ? 'inside' : 'dynamic_base');
    assert.equal(runtime.instance.exports.test_stack_top_0.value, initial + (inside ? 24 : 8),
        'fixed argument dynamic frame top differs');
    if (inside) {
        const first = Buffer.from(new Uint8Array(runtime.instance.exports.data_memory_1.buffer));
        const second = Buffer.from(new Uint8Array(runtime.instance.exports.data_memory_2.buffer));
        assert.equal(first.readUInt32LE(0), 1);
        assert.equal(first.readBigInt64LE(4), visits === 0 ? 1n : 9n,
            'fixed argument dynamic memory base differs');
        assert.equal(second.readBigInt64LE(4), visits === 0 ? 0n : 1n,
            'fixed argument dynamic memory base differs');
        if (visits === 1) assert.equal(second.readUInt32LE(0), 1);
    }
    visits++;
    fs.writeSync(1, bytes);
});
initial = runtime.instance.exports.test_stack_top_0.value;
runCompleted(runtime);
assert.equal(visits, 3);
assert.equal(runtime.instance.exports.test_stack_top_0.value, initial);
