// Direct runtime checks. Calls are synchronous; inspect the owning stack's
// top and memory only after allocation or failure has completed.
import assert from 'node:assert/strict';
import fs from 'node:fs';

const bytes = fs.readFileSync(process.argv[2]);
function instance(binary) {
    return new WebAssembly.Instance(new WebAssembly.Module(binary), { goose: {
        fail_v1(code) { throw new Error(`memory failure ${code}`); },
    } }).exports;
}
const pointer = (memory, offset) => (BigInt(memory) << 32n) | BigInt(offset);
const uleb = value => {
    const bytes = [];
    do { const byte = Number(value & 127n); value >>= 7n; bytes.push(byte | (value ? 128 : 0)); } while (value);
    return bytes;
};
const x = instance(bytes);
for (let memory = 0; memory < 3; memory++) {
    for (const value of [0n, 1n, 127n, 128n, 16383n, 16384n, (1n << 32n) - 1n,
                         (1n << 63n) - 1n, 1n << 63n, (1n << 64n) - 1n]) {
        const encoded = uleb(value);
        new Uint8Array(x[`memory${memory}`].buffer).set(encoded, 6000);
        assert.deepEqual(x.read_prefix(pointer(memory, 6000)), [BigInt.asIntN(64, value), encoded.length]);
    }
    for (const malformed of [[128, 0], [...Array(9).fill(255), 2], Array(10).fill(128)]) {
        new Uint8Array(x[`memory${memory}`].buffer).set(malformed, 6000);
        assert.throws(() => x.read_prefix(pointer(memory, 6000)), /memory failure 13/);
    }
    const last = x[`memory${memory}`].buffer.byteLength - 1;
    new Uint8Array(x[`memory${memory}`].buffer)[last] = 128;
    assert.throws(() => x.read_prefix(pointer(memory, last)), WebAssembly.RuntimeError);
}
assert.throws(() => x.read_prefix(pointer(3, 6000)), /memory failure 7/);
assert.throws(() => x.read_prefix(pointer(0, 0xffffffff)), WebAssembly.RuntimeError);
assert.equal(x.top(1), 1);
assert.equal(x.top(2), 1);
assert.equal(x.reserve1(64), 1);
assert.equal(x.reserve(2, 64), 1);
for (let memory = 0; memory < 3; memory++) {
    const p = pointer(memory, 17);
    const marker = -(1n << 63n) + BigInt(memory);
    x.store64(pointer(memory, 3), marker);
    x.store64(p, 0x1234567887654321n);
    assert.equal(x.load64(p), 0x1234567887654321n);
    x.store8(p, 255n);
    assert.equal(x.load8s(p), -1n);
    assert.equal(x.load8u(p), 255n);
    x.store16(p, 0x8001n);
    assert.equal(x.load16s(p), -32767n);
    assert.equal(x.load16u(p), 32769n);
    x.store32(p, 0x80000001n);
    assert.equal(x.load32s(p), -2147483647n);
    assert.equal(x.load32u(p), 2147483649n);
    x.storef32(p, 0.1);
    assert.equal(x.loadf32(p), Math.fround(0.1));
    x.storef64(pointer(memory, 33), -0);
    assert(Object.is(x.loadf64(pointer(memory, 33)), -0));
    x.storebool(pointer(memory, 41), 1);
    assert.equal(x.loadbool(pointer(memory, 41)), 1);
    assert.equal(x.load64(pointer(memory, 3)), marker);
}
for (let memory = 0; memory < 3; memory++)
    assert.equal(x.load64(pointer(memory, 3)), -(1n << 63n) + BigInt(memory));

const pattern = new Uint8Array([0, 127, 128, 255]);
new Uint8Array(x.memory0.buffer).set(pattern, 100);
for (let memory = 0; memory < 3; memory++) {
    x.copy_from_frame(pointer(memory, 1000), 100, pattern.length);
    assert.deepEqual(new Uint8Array(x[`memory${memory}`].buffer, 1000, 4), pattern);
}
x.copy_from_frame(pointer(2, 65536), 65536, 0);
for (const memory of [3, 0xffffffff])
    assert.throws(() => x.copy_from_frame(pointer(memory, 1000), 100, 4), /memory failure 7/);
assert.throws(() => x.copy_from_frame(pointer(2, 1000), 65535, 2), WebAssembly.RuntimeError);
assert.deepEqual(new Uint8Array(x.memory2.buffer, 1000, 4), pattern);
x.store8(pointer(2, 65535), 90n);
assert.throws(() => x.copy_from_frame(pointer(2, 65535), 100, 2), WebAssembly.RuntimeError);
assert.equal(x.load8u(pointer(2, 65535)), 90n);
for (let memory = 0; memory < 3; memory++) {
    x.store32(pointer(memory, 2000), 17n);
    x.store32off(pointer(memory, 2000), 0xffffffffn);
    assert.equal(x.load32u(pointer(memory, 2000)), 17n);
    assert.equal(x.load32off(pointer(memory, 2000)), 0xffffffffn);
}
assert.throws(() => x.load32huge(pointer(0, 0)), WebAssembly.RuntimeError);
assert.throws(() => x.load32off(pointer(3, 2000)), /memory failure 7/);
assert.throws(() => x.load32off(pointer(2, 65532)), WebAssembly.RuntimeError);
for (let memory = 0; memory < 3; memory++)
    new Uint8Array(x[`memory${memory}`].buffer).set([memory, 0, 127, 255], 3000);
for (let source = 0; source < 3; source++) for (let destination = 0; destination < 3; destination++) {
    x.copy(pointer(destination, 4000), pointer(source, 3000), 4);
    assert.deepEqual([...new Uint8Array(x[`memory${destination}`].buffer, 4000, 4)], [source, 0, 127, 255]);
}
const overlap = new Uint8Array(x.memory1.buffer);
overlap.set([1, 2, 3, 4, 5], 5000);
x.copy(pointer(1, 5001), pointer(1, 5000), 4);
assert.deepEqual([...overlap.subarray(5000, 5005)], [1, 1, 2, 3, 4]);
x.copy(pointer(1, 5000), pointer(1, 5001), 4);
assert.deepEqual([...overlap.subarray(5000, 5004)], [1, 2, 3, 4]);
assert.throws(() => x.copy(pointer(3, 4000), pointer(0, 3000), 4), /memory failure 7/);
assert.throws(() => x.copy(pointer(0, 4000), pointer(3, 3000), 4), /memory failure 7/);
assert.throws(() => x.copy(pointer(2, 4000), pointer(0, 65535), 2), WebAssembly.RuntimeError);
assert.deepEqual([...new Uint8Array(x.memory2.buffer, 4000, 4)], [2, 0, 127, 255]);

assert.equal(x.reserve1(65536 - 65), 65);
assert.equal(x.top(1), 65536);
assert.equal(x.memory1.buffer.byteLength, 65536);
assert.equal(x.reserve1(1), 65536);
assert.equal(x.memory1.buffer.byteLength, 131072);
assert.equal(x.memory2.buffer.byteLength, 65536);
assert.equal(x.load64(pointer(1, 3)), -(1n << 63n) + 1n);
assert.equal(x.reserve2(131072), 65);
assert.equal(x.memory2.buffer.byteLength, 196608);
assert.equal(x.memory1.buffer.byteLength, 131072);
assert.equal(x.load64(pointer(2, 3)), -(1n << 63n) + 2n);
x.restore(1, 65);
assert.equal(x.top(1), 65);
assert.equal(x.reserve1(1), 65);
const saved = x.top(1);
assert.throws(() => x.reserve1(-1), /memory failure 6/);
assert.equal(x.top(1), saved);
assert.equal(x.memory1.buffer.byteLength, 131072);
assert.throws(() => x.restore(1, 0), /memory failure 7/);
assert.throws(() => x.restore(2, x.memory2.buffer.byteLength + 1), /memory failure 7/);
assert.equal(x.top(1), saved);
for (const memory of [0, 3, -1]) {
    assert.throws(() => x.reserve(memory, 1), /memory failure 7/);
    assert.throws(() => x.top(memory), /memory failure 7/);
}
for (const memory of [3, 0xffffffff])
    assert.throws(() => x.load64(pointer(memory, 3)), /memory failure 7/);
assert.throws(() => x.load64(pointer(2, x.memory2.buffer.byteLength)), WebAssembly.RuntimeError);

// Limit only Memory 1 in a derived test module. A real memory.grow failure
// must preserve its previous top, contents, and the other memory's state.
function limited(binary) {
    let pos = 8;
    const read = () => {
        let n = 0, shift = 0, b;
        do { b = binary[pos++]; n += (b & 127) * 2 ** shift; shift += 7; } while (b & 128);
        return n;
    };
    const encode = n => {
        const result = [];
        do { const b = n % 128; n = Math.floor(n / 128); result.push(b | (n ? 128 : 0)); } while (n);
        return result;
    };
    const output = [...binary.subarray(0, 8)];
    while (pos < binary.length) {
        const id = binary[pos++], length = read(), end = pos + length;
        if (id === 5) {
            const count = read(), body = [...encode(count)];
            for (let i = 0; i < count; i++) {
                const flags = read(), min = read(), max = read();
                assert.equal(flags, 1);
                body.push(...encode(flags), ...encode(min), ...encode(i === 1 ? 1 : max));
            }
            output.push(id, ...encode(body.length), ...body);
        } else output.push(id, ...encode(length), ...binary.subarray(pos, end));
        pos = end;
    }
    return new Uint8Array(output);
}
const limitedBytes = limited(bytes);
if (process.argv[3]) fs.writeFileSync(process.argv[3], limitedBytes);
const y = instance(limitedBytes);
assert.equal(y.reserve1(65535), 1);
y.store64(pointer(1, 3), 12345n);
assert.throws(() => y.reserve1(1), /memory failure 6/);
assert.equal(y.top(1), 65536);
assert.equal(y.memory1.buffer.byteLength, 65536);
assert.equal(y.memory2.buffer.byteLength, 65536);
assert.equal(y.load64(pointer(1, 3)), 12345n);
console.log('Wasm data-memory runtime checks passed');
