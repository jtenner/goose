import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';
let runtime, initial, visits = 0;
runtime = instantiate(fs.readFileSync(process.argv[2]), bytes => {
    const label = Buffer.from(bytes).toString('utf8').trim();
    assert.equal(runtime.instance.exports.test_stack_top_0.value, initial + 32,
        'fixed array conversion namespace frame top differs');
    const tops = [1, 2].map(n => runtime.instance.exports[`test_stack_top_${n}`].value);
    assert.deepEqual(tops, visits === 0 ? [21, 1] : visits === 1 ? [37, 21] : [1, 1],
        'fixed array conversion namespace tops differ');
    assert.equal(label, visits < 2 ? 'inside' : 'namespaces'); visits++;
    assert.equal(runtime.pendingPrints, 0); fs.writeSync(1, bytes);
});
initial = runtime.instance.exports.test_stack_top_0.value;
runCompleted(runtime); assert.equal(visits, 3);
assert.equal(runtime.instance.exports.test_stack_top_0.value, initial);
for (const n of [1, 2]) assert.equal(runtime.instance.exports[`test_stack_top_${n}`].value, 1);
