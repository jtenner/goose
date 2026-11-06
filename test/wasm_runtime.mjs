// Resource-owner checks run at the print completion signal, before _start ends.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate, GooseFailure } from '../scripts/run_wasm.mjs';

const [modulePath, mode] = process.argv.slice(2);
let runtime;
const output = [];
runtime = instantiate(fs.readFileSync(modulePath), bytes => {
    assert.equal(runtime.pendingPrints, 0, 'an abandoned print buffer remains live');
    output.push(bytes);
});
if (mode === 'growth-failure') {
    assert.throws(() => runtime.run(), /out of memory growing frame storage/);
    assert.equal(runtime.pendingPrints, 0);
    assert.equal(runtime.instance.exports.memory.buffer.byteLength, 65536);
} else {
    runtime.run();
    assert.equal(runtime.pendingPrints, 0);
    if (mode === 'growth') assert.equal(runtime.instance.exports.memory.buffer.byteLength, 131072);
    assert.throws(() => runtime.run(), GooseFailure);
    process.stdout.write(Buffer.concat(output));
}
