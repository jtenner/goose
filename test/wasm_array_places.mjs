// Synthetic private-service inputs are not new source-layout admission.
import assert from 'node:assert/strict';
import fs from 'node:fs';
const x = new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[2])), {
    goose: { fail_v1(code) { throw new Error(`place failure ${code}`); } },
}).exports;
const p = (memory, offset) => (BigInt(memory) << 32n) | BigInt(offset);
for (const value of [0, 1, 16, 0xffffffff]) {
    assert.equal(x.pack0(value), BigInt(value));
    assert.equal(x.pack2(value), p(2, value));
}
assert.equal(x.packconstant(), p(2, 32));
assert.equal(x.pack2off(16), p(2, 23));
assert.equal(x.pack2bounded(16), p(2, 23));
assert.equal(x.packedoff(p(1, 16)), p(1, 23));
assert.equal(x.knownoff(p(2, 16)), 23);
assert.equal(x.thin0(p(0, 16)), 23);
assert.throws(() => x.pack2off(0xfffffffe), /place failure 11/);
assert.throws(() => x.packedoff(p(1, 0xfffffffe)), /place failure 11/);
assert.throws(() => x.knownoff(p(2, 0xfffffffe)), /place failure 11/);
assert.throws(() => x.thin0(p(1, 16)), /place failure 7/);
const data = new DataView(x.memory2.buffer);
data.setUint32(19, 32, true); data.setUint32(23, 3, true);
for (const mode of ['thin', 'known', 'dynamic']) {
    const address = mode === 'thin' ? 16 : p(2, 16);
    assert.equal(x[`${mode}cap`](address), 32n);
    assert.equal(x[`${mode}len`](address), 3n);
    for (let index = 0; index < 3; index++)
        assert.equal(x[`${mode}element`](address, BigInt(index)), p(2, 27 + index), `${mode} element lost its memory identity`);
    x[`${mode}store`](address, 2n); assert.equal(data.getUint32(23, true), 2);
    data.setUint32(23, 3, true);
}
const bytes = [x.memory0, x.memory1, x.memory2].map(m => new Uint8Array(m.buffer));
for (const [name, d, s] of [['copy00', 0, 0], ['copy20', 2, 0], ['copy02', 0, 2],
                          ['copy0u', 0, 1], ['copyu0', 1, 0], ['copy2u', 2, 1],
                          ['copyu2', 1, 2], ['copyuu', 1, 2], ['copyuu', 2, 2]]) {
    bytes.forEach((b, m) => b.fill(40 + m, 256, 320));
    bytes[s].set([1, 2, 3, 4, 5, 6, 7, 8], 256);
    const before = bytes.map(b => b.slice());
    const expected = before.map(b => b.slice()); expected[d].set(before[s].slice(256, 264), d === s ? 258 : 280);
    x[name](p(d, d === s ? 258 : 280), p(s, 256), 8);
    bytes.forEach((b, m) => assert.deepEqual(b, expected[m], name));
}
bytes[2].set([11, 12, 13, 14], 32); x.copyconstant(p(1, 400));
assert.deepEqual([...bytes[1].slice(400, 404)], [11, 12, 13, 14]);
for (const [destination, source, count, reason] of [
    [p(3, 256), p(1, 256), 8, /place failure 7/],
    [p(1, 256), p(3, 256), 8, /place failure 7/],
    [p(1, 65534), p(2, 256), 8, WebAssembly.RuntimeError],
    [p(1, 256), p(2, 65534), 8, WebAssembly.RuntimeError],
]) {
    const before = bytes.map(b => b.slice());
    assert.throws(() => x.copyuu(destination, source, count), reason);
    bytes.forEach((b, m) => assert.deepEqual(b, before[m], 'failed copy changed memory'));
}
console.log('array places: PASS');
