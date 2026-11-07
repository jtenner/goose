import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';
const [file, mainSize, walkSize] = process.argv.slice(2);
let runtime, initial, visits = 0;
runtime = instantiate(fs.readFileSync(file), bytes => {
    const text = Buffer.from(bytes).toString('utf8').trim();
    const match = /^(enter|exit)=(\d)$/.exec(text);
    const expected = initial + Number(mainSize) + (match ? (4 - Number(match[2])) * Number(walkSize) : 0);
    assert.equal(runtime.instance.exports.test_stack_top_0.value, expected,
        'recursive copied-binder frame top differs at the live checkpoint');
    assert.equal(runtime.pendingPrints, 0);
    visits++; fs.writeSync(1, bytes);
});
initial = runtime.instance.exports.test_stack_top_0.value;
runCompleted(runtime);
assert.equal(visits, 9);
assert.equal(runtime.instance.exports.test_stack_top_0.value, initial,
    'recursive copied-binder frame top was not restored');
