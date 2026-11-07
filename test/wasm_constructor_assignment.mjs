// Observe temporary ownership while the guest is active and after completion.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';
const [file, mode, frame = '0', temporary = '8'] = process.argv.slice(2);
let runtime, initial, visits = 0;
runtime = instantiate(fs.readFileSync(file), bytes => {
    const line = Buffer.from(bytes).toString('utf8').trim();
    const nested = mode === 'nested_assignment';
    const live = nested ? (line === 'nested-live' ? 2 * Number(temporary) : line === 'nested-done' ? Number(temporary) : 0) : (mode === 'early' || mode === 'exits') && line === 'inner' ? Number(temporary) : 0;
    assert.equal(runtime.instance.exports.test_stack_top_0.value,
        initial + Number(frame) + live, 'constructor temporary live frame top differs');
    assert.equal(runtime.pendingPrints, 0);
    visits++;
    fs.writeSync(1, bytes);
});
initial = runtime.instance.exports.test_stack_top_0.value;
runCompleted(runtime);
assert.equal(visits, mode === 'nested_assignment' ? 3 : mode === 'exits' ? 11 : mode === 'early' || mode === 'loop' ? 5 : 1);
assert.equal(runtime.instance.exports.test_stack_top_0.value, initial,
    'constructor temporary frame top was not restored');
