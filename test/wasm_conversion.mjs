// In-range scalar casts must not cross the host boundary. Fallback correctness
// is checked separately against native C in wasm_conversion_boundaries.goose.
import assert from 'node:assert/strict';
import fs from 'node:fs';
const module = new WebAssembly.Module(fs.readFileSync(process.argv[2]));
const callbacks = { goose: {} };
let conversions = 0;
for (const entry of WebAssembly.Module.imports(module)) {
    callbacks.goose[entry.name] = (...args) => {
        if (entry.name === 'float_to_int_v1') {
            conversions++;
            throw new Error('in-range conversion crossed the host boundary');
        }
        throw new Error(`unexpected host call: ${entry.name} (${args[0] ?? ''})`);
    };
}
const instance = new WebAssembly.Instance(module, callbacks);
instance.exports._start();
assert.equal(conversions, 0);
