// Check a host-owned guard at print completion while the activation is live.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate } from '../scripts/run_wasm.mjs';

let runtime, initial, end, completions = 0;
runtime = instantiate(fs.readFileSync(process.argv[2]), bytes => {
    assert.equal(runtime.pendingPrints, 0);
    assert.equal(runtime.instance.exports.test_frame_top.value, end,
                 'guard was observed outside the active constructor owner');
    assert.deepEqual([...new Uint8Array(runtime.instance.exports.memory.buffer, end, 8)],
                     Array(8).fill(165), 'aggregate constructor crossed its planned owner image');
    completions++;
    fs.writeSync(1, bytes);
});
initial = runtime.instance.exports.test_frame_top.value;
end = initial + Number(process.argv[3]);
new Uint8Array(runtime.instance.exports.memory.buffer).fill(165, end, end + 8);
runtime.run();
assert.equal(completions, 1, 'missing constructor completion signal');
assert.equal(runtime.instance.exports.test_frame_top.value, initial);
