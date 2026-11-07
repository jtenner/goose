// Record completed instances for parent/candidate ABI comparisons.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { instantiate } from '../scripts/run_wasm.mjs';

export function runCompleted(runtime, state = {}) {
    runtime.run(() => {
        state.completed = true;
        state.completionCalls = (state.completionCalls ?? 0) + 1;
        state.pendingPrints = runtime.pendingPrints;
        state.pendingSnapshots = runtime.pendingSnapshots;
        assert.equal(state.pendingPrints, 0, 'completed instance retains a print owner');
        assert.equal(state.pendingSnapshots, 0, 'completed instance retains a snapshot owner');
    });
    assert.equal(state.completed, true, 'guest completion observer did not run');
    assert.equal(state.completionCalls, 1, 'guest completion observer ran more than once');
    return state;
}

function main() {
    const [modulePath, out] = process.argv.slice(2);
    assert(modulePath && out, 'module and snapshot directory are required');
    const output = [];
    const runtime = instantiate(fs.readFileSync(modulePath), bytes => output.push(bytes));
    let completion;
    try { completion = runCompleted(runtime); }
    finally { process.stdout.write(Buffer.concat(output)); }
    fs.mkdirSync(out, { recursive: true });
    const memories = [], globals = [];
    for (const [name, value] of Object.entries(runtime.instance.exports)) {
        if (value instanceof WebAssembly.Memory) {
            const bytes = Buffer.from(value.buffer);
            fs.writeFileSync(path.join(out, `${name}.bin`), bytes);
            memories.push({ name, bytes: bytes.length, sha256: crypto.createHash('sha256').update(bytes).digest('hex') });
        } else if (value instanceof WebAssembly.Global) {
            globals.push({ name, value: String(value.value) });
        }
    }
    assert(memories.some(m => m.name === 'memory'), 'completed instance has no Memory 0');
    fs.writeFileSync(path.join(out, 'instance.json'), JSON.stringify({ ...completion, memories, globals }, null, 2) + '\n');
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
