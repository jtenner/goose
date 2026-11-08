import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';
let runtime, initial, heads = 0, finished = 0;
runtime = instantiate(fs.readFileSync(process.argv[2]), bytes => {
    assert.equal(runtime.instance.exports.test_stack_top_0.value, initial + 16,
        'fixed negation loop live frame top differs');
    const label = Buffer.from(bytes).toString('utf8').trim();
    if (label === 'head') heads++;
    else { assert.equal(label, 'loop_exit'); finished++; }
    assert.equal(runtime.pendingPrints, 0);
    fs.writeSync(1, bytes);
});
initial = runtime.instance.exports.test_stack_top_0.value;
runCompleted(runtime);
assert.equal(heads, 4); assert.equal(finished, 1);
assert.equal(runtime.instance.exports.test_stack_top_0.value, initial);
