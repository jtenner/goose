import assert from 'node:assert/strict';
import fs from 'node:fs';
const x = new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[2])), {
    goose: { fail_v1(code) { throw new Error(`memory failure ${code}`); } },
}).exports;
const count = 65;
const pointer = (memory, offset) => (BigInt(memory) << 32n) | BigInt(offset);
for (let i = 0; i < count; i++) {
    new Uint8Array(x[`memory${i}`].buffer).set([128, 1], 500);
    assert.deepEqual(x.read_prefix(pointer(i, 500)), [128n, 2]);
    const bytes = new Uint8Array(x[`memory${i}`].buffer);
    bytes.fill(90, 699, 705);
    x.fill(pointer(i, 700), 0x1ab, 4);
    assert.deepEqual([...bytes.slice(699, 705)], [90, 171, 171, 171, 171, 90]);
}
assert.throws(() => x.read_prefix(pointer(count, 500)), /memory failure 7/);
const last = new Uint8Array(x.memory64.buffer);
const beforeFillFailure = Buffer.from(last);
x.fill(pointer(64, 65536), 7, 0);
assert.throws(() => x.fill(pointer(64, 65535), 7, 2), WebAssembly.RuntimeError);
for (const invalid of [count, 0xffffffff])
    assert.throws(() => x.fill(pointer(invalid, 700), 7, 0), /memory failure 7/);
assert.deepEqual(Buffer.from(last), beforeFillFailure);
for (let i = 0; i < count; i++) new Uint8Array(x[`memory${i}`].buffer).set([i, 0, 127, 255], 100);
for (let source = 0; source < count; source++) for (let destination = 0; destination < count; destination++) {
    x.copy(pointer(destination, 200), pointer(source, 100), 4);
    assert.deepEqual([...new Uint8Array(x[`memory${destination}`].buffer, 200, 4)], [source, 0, 127, 255]);
}
for (let source = 0; source < count; source++) {
    const frame = new Uint8Array(x.memory0.buffer);
    frame.fill(91, 299, 305);
    x.copy_to_frame(300, pointer(source, 100), 4);
    assert.deepEqual([...frame.slice(299, 305)], [91, source, 0, 127, 255, 91]);
}
x.copy_to_frame(65536, pointer(64, 65536), 0);
const frame = new Uint8Array(x.memory0.buffer);
frame.fill(91, 299, 305);
for (const invalid of [count, 0xffffffff]) {
    assert.throws(() => x.copy_to_frame(300, pointer(invalid, 100), 4), /memory failure 7/);
    assert.deepEqual([...frame.slice(299, 305)], [91, 91, 91, 91, 91, 91]);
}
assert.throws(() => x.copy_to_frame(300, pointer(64, 65535), 2), WebAssembly.RuntimeError);
assert.deepEqual([...frame.slice(299, 305)], [91, 91, 91, 91, 91, 91]);
frame[65535] = 92;
assert.throws(() => x.copy_to_frame(65535, pointer(64, 100), 2), WebAssembly.RuntimeError);
assert.equal(frame[65535], 92);
frame.set([1, 2, 3, 4, 5], 400);
x.copy_to_frame(401, pointer(0, 400), 4);
assert.deepEqual([...frame.slice(400, 405)], [1, 1, 2, 3, 4]);
x.copy(pointer(64, 65536), pointer(63, 65536), 0);
assert.throws(() => x.copy(pointer(count, 200), pointer(0, 100), 4), /memory failure 7/);
assert.throws(() => x.copy(pointer(0, 200), pointer(count, 100), 4), /memory failure 7/);
assert.throws(() => x.copy(pointer(64, 200), pointer(0, 65535), 2), WebAssembly.RuntimeError);
assert.deepEqual([...new Uint8Array(x.memory64.buffer, 200, 4)], [64, 0, 127, 255]);
x.store8(pointer(64, 65535), 90n);
assert.throws(() => x.copy(pointer(64, 65535), pointer(0, 100), 2), WebAssembly.RuntimeError);
assert.equal(x.load8u(pointer(64, 65535)), 90n);
console.log('65-memory copy matrix passed');
