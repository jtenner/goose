// Controls for complete reservation before data-array child initialization.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { instantiate, GooseFailure } from '../scripts/run_wasm.mjs';
const [modulePath, mode, resultPath, expectedLine] = process.argv.slice(2);
let runtime, observed = false, before, output = [];
const all = () => Object.entries(runtime.instance.exports).filter(([, x]) => x instanceof WebAssembly.Memory);
const tops = () => Object.entries(runtime.instance.exports).filter(([n]) => n.startsWith('test_stack_top_')).map(([n, x]) => [n, x.value]);
runtime = instantiate(fs.readFileSync(modulePath), bytes => {
    output.push(Buffer.from(bytes));
    if (bytes.toString() !== 'ready\n') return;
    assert.equal(observed, false); observed = true;
    const x = runtime.instance.exports;
    assert.equal(x.test_stack_top_1.value, 1);
    if (mode.startsWith('growth')) new Uint8Array(x.data_memory_1.buffer).fill(0xaa);
    if (mode === 'overflow') {
        const source = new DataView(x.data_memory_2.buffer);
        assert.equal(source.getUint32(1, true), 1); assert.equal(source.getUint32(5, true), 11);
        source.setUint32(1, 0xffffffff, true);
    }
    before = { tops: tops(), memories: all().map(([n, x]) => [n, Buffer.from(x.buffer)]) };
});
const failure = mode === 'overflow' || mode === 'growth-failure' || mode === 'growth-bad-zero';
if (failure) {
    if (mode === 'growth-bad-zero') {
        assert.throws(() => runtime.run(), e => e instanceof GooseFailure && e.message.includes('assert failed') && e.message.endsWith(':' + expectedLine));
        assert.equal(new Uint8Array(runtime.instance.exports.data_memory_1.buffer)[40005], 0xaa);
    } else {
        assert.throws(() => runtime.run(), e => e instanceof GooseFailure && e.message.includes('out of memory growing data storage'));
        assert.equal(Buffer.concat(output).toString(), 'ready\n');
        assert.deepEqual(tops(), before.tops);
        for (const [name, bytes] of before.memories) assert.deepEqual(Buffer.from(runtime.instance.exports[name].buffer), bytes, name);
    }
} else {
    runtime.run();
    assert.equal(Buffer.concat(output).toString(), 'ready\nchild\nchild\ndone\n');
    assert.equal(runtime.instance.exports.test_stack_top_1.value, 1);
    const image = Buffer.from(runtime.instance.exports.data_memory_1.buffer);
    const model = Buffer.alloc(image.length); model[0] = 0xaa; model.writeUInt32LE(2, 1); model[5] = 3; model[40006] = 3;
    assert.deepEqual(image, model, 'dirty destination fields were not constructed in their real memory');
    for (const [name, x] of Object.entries(runtime.instance.exports)) if (/^test_stack_top_[1-9]/.test(name)) assert.equal(x.value, 1);
}
assert(observed); assert.equal(runtime.pendingPrints, 0); assert.equal(runtime.pendingSnapshots, 0);
fs.writeFileSync(resultPath, JSON.stringify({ mode, observedReady: observed, expectedFailure: failure, tops: tops(), allChecks: 'PASS' }, null, 2) + '\n');
process.stdout.write(failure ? 'allocation-control=ok\n' : Buffer.concat(output));
