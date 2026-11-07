// Derived test modules export stack tops; production modules do not.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';

const mode = process.argv[3];
let runtime, initial, end, completions = 0;
const seen = [];
runtime = instantiate(fs.readFileSync(process.argv[2]), bytes => {
    const exports = runtime.instance.exports;
    assert.equal(runtime.pendingPrints, 0);
    assert.equal(exports.test_stack_top_0.value, end, 'iteration checkpoint is outside its live frame');
    const text = Buffer.from(bytes).toString('utf8').trim();
    if (mode === 'copy') {
        assert.equal(text, 'iteration');
        assert.deepEqual([...new Uint8Array(exports.memory.buffer, end, 8)],
                         Array(8).fill(165), 'iteration copy crossed its planned owner image');
    } else if (mode === 'zero') {
        assert.equal(text, 'empty');
        assert.deepEqual([...new Uint8Array(exports.memory.buffer, initial + 8, 7)],
                         Array(7).fill(165), 'zero-trip iteration copied an element');
    } else {
        assert.equal(mode, 'cleanup');
        assert.equal(exports.test_stack_top_1.value, 17, 'live outer data owner was lost');
        assert.equal(exports.test_stack_top_2.value,
                     text === 'inner' || text === 'continue' ? 17 : 1,
                     'iteration body data top was not restored at its completion');
        assert.equal(new DataView(exports.data_memory_1.buffer).getBigInt64(9, true), 91n);
        seen.push(text);
    }
    completions++;
    fs.writeSync(1, bytes);
});
const exports = runtime.instance.exports;
initial = exports.test_stack_top_0.value;
end = initial + (mode === 'copy' ? 21 : mode === 'zero' ? 15 : 24);
if (mode === 'copy') new Uint8Array(exports.memory.buffer).fill(165, end, end + 8);
if (mode === 'zero') {
    const memory = new Uint8Array(exports.memory.buffer);
    memory.fill(34, initial + 1, initial + 8);
    memory.fill(165, initial + 8, initial + 15);
}
runtime.run();
assert.equal(exports.test_stack_top_0.value, initial, 'iteration activation top was not restored');
assert.equal(completions, mode === 'copy' ? 2 : mode === 'zero' ? 1 : 6);
if (mode === 'cleanup') {
    assert.deepEqual(seen, ['inner', 'restored', 'continue', 'inner', 'restored', 'after']);
    assert.equal(exports.test_stack_top_1.value, 1);
    assert.equal(exports.test_stack_top_2.value, 1);
}
