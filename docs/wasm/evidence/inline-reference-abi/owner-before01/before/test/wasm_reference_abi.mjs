// Record completed instances for parent/candidate ABI comparisons.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { instantiate } from '../scripts/run_wasm.mjs';

const [modulePath, out] = process.argv.slice(2);
assert(modulePath && out, 'module and snapshot directory are required');
const output = [];
const runtime = instantiate(fs.readFileSync(modulePath), bytes => output.push(bytes));
runtime.run();
assert.equal(runtime.pendingPrints, 0, 'completed instance retains a print owner');
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
fs.writeFileSync(path.join(out, 'instance.json'), JSON.stringify({ completed: true, pendingPrints: 0, memories, globals }, null, 2) + '\n');
process.stdout.write(Buffer.concat(output));
