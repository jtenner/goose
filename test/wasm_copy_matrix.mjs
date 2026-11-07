import assert from 'node:assert/strict';
import fs from 'node:fs';
const x = new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[2])), {
    goose: { fail_v1(code) { throw new Error(`memory failure ${code}`); } },
}).exports;
const count = 65;
const pointer = (memory, offset) => (BigInt(memory) << 32n) | BigInt(offset);
for (let i = 0; i < count; i++) new Uint8Array(x[`memory${i}`].buffer).set([i, 0, 127, 255], 100);
for (let source = 0; source < count; source++) for (let destination = 0; destination < count; destination++) {
    x.copy(pointer(destination, 200), pointer(source, 100), 4);
    assert.deepEqual([...new Uint8Array(x[`memory${destination}`].buffer, 200, 4)], [source, 0, 127, 255]);
}
x.copy(pointer(64, 65536), pointer(63, 65536), 0);
assert.throws(() => x.copy(pointer(count, 200), pointer(0, 100), 4), /memory failure 7/);
assert.throws(() => x.copy(pointer(0, 200), pointer(count, 100), 4), /memory failure 7/);
assert.throws(() => x.copy(pointer(64, 200), pointer(0, 65535), 2), WebAssembly.RuntimeError);
assert.deepEqual([...new Uint8Array(x.memory64.buffer, 200, 4)], [64, 0, 127, 255]);
x.store8(pointer(64, 65535), 90n);
assert.throws(() => x.copy(pointer(64, 65535), pointer(0, 100), 2), WebAssembly.RuntimeError);
assert.equal(x.load8u(pointer(64, 65535)), 90n);
console.log('65-memory copy matrix passed');
