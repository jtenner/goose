import assert from 'node:assert/strict';
import { pathToFileURL } from 'node:url';
const helper = process.argv[2] ? pathToFileURL(process.argv[2]).href : new URL('./wasm_memory_snapshot.mjs', import.meta.url).href;
const { snapshotMemory } = await import(helper);
for (const mode of (process.argv[3] ? [process.argv[3]] : ['write', 'grow'])) {
    const memory = new WebAssembly.Memory({ initial: 1 });
    new Uint8Array(memory.buffer)[5] = 11;
    const before = snapshotMemory(memory);
    if (mode === 'write') {
        new Uint8Array(memory.buffer)[5] = 12;
        assert.equal(before[5], 11, 'snapshot changed after a later write');
    } else {
        assert.equal(mode, 'grow');
        memory.grow(1);
        assert.equal(before.byteLength, 65536, 'snapshot lost its bytes after memory growth');
        assert.equal(before[5], 11, 'snapshot changed after memory growth');
    }
}
console.log('snapshot=ok');
