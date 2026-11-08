import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';
const [file, mode] = process.argv.slice(2);
let runtime, initial, visits = 0;
runtime = instantiate(fs.readFileSync(file), bytes => {
    const line = Buffer.from(bytes).toString('utf8').trim();
    const extra = line === 'nested-live' ? 32 :
        ['live', 'inner', 'nested-done'].includes(line) ? 16 : 0;
    assert.equal(runtime.instance.exports.test_stack_top_0.value, initial + extra,
        'array constructor temporary live frame top differs');
    assert.equal(runtime.pendingPrints, 0);
    visits++;
    fs.writeSync(1, bytes);
});
initial = runtime.instance.exports.test_stack_top_0.value;
runCompleted(runtime);
assert.equal(visits, mode === 'loop' ? 9 : mode === 'early_owner' ? 2 : 3);
assert.equal(runtime.instance.exports.test_stack_top_0.value, initial,
    'array constructor temporary was not restored');
