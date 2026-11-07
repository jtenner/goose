import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { instantiate } from '../scripts/run_wasm.mjs';
import { runCompleted } from './wasm_reference_abi.mjs';

const [healthy, controls, expectedPath, resultPath] = process.argv.slice(2);
assert(healthy && controls && expectedPath && resultPath);
const expected = fs.readFileSync(expectedPath);
const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const manifest = JSON.parse(fs.readFileSync(path.join(controls, 'controls.json')));
assert.equal(hash(fs.readFileSync(healthy)), manifest.healthy_sha256);
const rows = [];
let baseline;
for (const mode of ['healthy', 'print-owner', 'snapshot-owner']) {
    const modulePath = mode === 'healthy' ? healthy : path.join(controls, `${mode}.wasm`);
    const bytes = fs.readFileSync(modulePath);
    if (mode !== 'healthy') {
        assert.equal(hash(bytes), manifest.controls.find(c => c.name === mode).sha256);
    }
    const output = [];
    const runtime = instantiate(bytes, chunk => output.push(chunk));
    const state = {};
    let failure;
    try { runCompleted(runtime, state); }
    catch (error) { failure = error; }
    assert.deepEqual(Buffer.concat(output), expected, `${mode}: guest output changed`);
    assert.equal(state.completed, true, `${mode}: guest did not return normally`);
    assert.equal(state.completionCalls, 1);
    const counts = mode === 'print-owner' ? [1, 0] : mode === 'snapshot-owner' ? [0, 1] : [0, 0];
    assert.deepEqual([state.pendingPrints, state.pendingSnapshots], counts);
    if (mode === 'healthy') assert.equal(failure, undefined);
    else {
        assert.equal(failure?.code, 'ERR_ASSERTION', 'wrong failure kind');
        assert.equal(failure.actual, 1); assert.equal(failure.expected, 0);
        const kind = mode === 'print-owner' ? 'print' : 'snapshot';
        assert(failure.message.includes(`completed instance retains a ${kind} owner`), 'wrong failure reason');
    }
    assert.equal(runtime.pendingPrints, 0, 'terminal cleanup retained print owners');
    assert.equal(runtime.pendingSnapshots, 0, 'terminal cleanup retained snapshot owners');
    assert.throws(() => runtime.run(), /only once/);
    const memories = Object.entries(runtime.instance.exports)
        .filter(([, value]) => value instanceof WebAssembly.Memory)
        .map(([name, value]) => ({ name, bytes: Buffer.from(new Uint8Array(value.buffer)) }));
    assert(memories.some(m => m.name === 'memory'));
    if (mode === 'healthy') baseline = memories;
    else assert.deepEqual(memories, baseline, `${mode}: guest memory changed`);
    rows.push({ mode, observedBeforeCleanup: state, terminalOwners: [runtime.pendingPrints, runtime.pendingSnapshots],
        expectedOutput: true, memoryMatchesHealthy: true, intendedAssertion: mode === 'healthy' ? null : failure.message,
        memories: memories.map(m => ({ name: m.name, bytes: m.bytes.length, sha256: hash(m.bytes) })) });
}
fs.writeFileSync(resultPath, JSON.stringify(rows, null, 2) + '\n');
console.log('reference ABI owner controls: 3 passed');
