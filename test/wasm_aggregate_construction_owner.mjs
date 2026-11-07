import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';
const [file, frame, lines, temporary = '8'] = process.argv.slice(2);
let runtime, initial, seen = 0;
runtime = instantiate(fs.readFileSync(file), bytes => {
    const evaluating = Buffer.from(bytes).toString('utf8') === 'eval\n';
    assert.equal(runtime.instance.exports.test_stack_top_0.value,
        initial + Number(frame) + (evaluating ? Number(temporary) : 0),
        'aggregate construction live frame top differs');
    assert.equal(runtime.pendingPrints, 0);
    seen++;
    fs.writeSync(1, bytes);
});
initial = runtime.instance.exports.test_stack_top_0.value;
runCompleted(runtime);
assert.equal(seen, Number(lines));
assert.equal(runtime.instance.exports.test_stack_top_0.value, initial,
    'aggregate construction frame top was not restored');
