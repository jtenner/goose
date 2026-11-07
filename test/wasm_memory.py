#!/usr/bin/env python3
"""Check the data-memory runtime under Wasmtime, without timing."""
import math
from pathlib import Path
import sys
import wasmtime


def instance(path):
    config = wasmtime.Config()
    config.wasm_multi_memory = True
    engine = wasmtime.Engine(config)
    module = wasmtime.Module(engine, Path(path).read_bytes())
    store = wasmtime.Store(engine)

    def fail(code, offset, length, line):
        raise RuntimeError(f'memory failure {code}')

    callback = wasmtime.Func(store, module.imports[0].type, fail)
    value = wasmtime.Instance(store, module, [callback])
    exports = value.exports(store)
    return store, exports


def throws(call, reason):
    try:
        call()
    except Exception as error:
        assert reason in str(error), error
    else:
        raise AssertionError(f'expected {reason}')


def main():
    store, exports = instance(sys.argv[1])
    for memory in range(3):
        for value in [0, 1, 127, 128, 16383, 16384, (1 << 32) - 1,
                      (1 << 63) - 1, 1 << 63, (1 << 64) - 1]:
            remaining, encoded = value, []
            while True:
                byte = remaining & 127
                remaining >>= 7
                encoded.append(byte | (128 if remaining else 0))
                if not remaining:
                    break
            exports[f'memory{memory}'].write(store, bytes(encoded), 6000)
            signed = value if value < 1 << 63 else value - (1 << 64)
            assert exports['read_prefix'](store, (memory << 32) | 6000) == [signed, len(encoded)]
        for malformed in [[128, 0], [255] * 9 + [2], [128] * 10]:
            exports[f'memory{memory}'].write(store, bytes(malformed), 6000)
            throws(lambda: exports['read_prefix'](store, (memory << 32) | 6000), 'memory failure 13')
        last = exports[f'memory{memory}'].data_len(store) - 1
        exports[f'memory{memory}'].write(store, bytes([128]), last)
        throws(lambda: exports['read_prefix'](store, (memory << 32) | last), 'out of bounds')
    throws(lambda: exports['read_prefix'](store, (3 << 32) | 6000), 'memory failure 7')
    throws(lambda: exports['read_prefix'](store, 0xffffffff), 'out of bounds')

    def call(name, *args):
        return exports[name](store, *args)

    def pointer(memory, offset):
        value = (memory << 32) | offset
        return value - (1 << 64) if value >= 1 << 63 else value

    def size(memory):
        return exports[f'memory{memory}'].data_len(store)

    assert call('top', 1) == call('top', 2) == 1
    assert call('reserve1', 64) == 1
    assert call('reserve', 2, 64) == 1
    for memory in range(3):
        address = pointer(memory, 17)
        call('store64', pointer(memory, 3), -(1 << 63) + memory)
        for bits in (8, 16, 32):
            value = (1 << (bits - 1)) + 1
            call(f'store{bits}', address, value)
            assert call(f'load{bits}s', address) == value - (1 << bits)
            assert call(f'load{bits}u', address) == value
        call('storef32', address, 0.5)
        assert call('loadf32', address) == 0.5
        call('storef64', pointer(memory, 33), -0.0)
        assert math.copysign(1.0, call('loadf64', pointer(memory, 33))) == -1.0
        call('storebool', pointer(memory, 41), 1)
        assert call('loadbool', pointer(memory, 41)) == 1
    for memory in range(3):
        assert call('load64', pointer(memory, 3)) == -(1 << 63) + memory
    pattern = bytes([0, 127, 128, 255])
    for memory in range(3):
        target = exports[f'memory{memory}']
        target.write(store, bytes([90] * 6), 6000)
        call('fill', pointer(memory, 6001), 0x1ab, 4)
        assert bytes(target.read(store, 6000, 6006)) == bytes([90, 171, 171, 171, 171, 90])
        call('fill', pointer(memory, 65536), 13, 0)
        before = bytes(target.read(store))
        throws(lambda: call('fill', pointer(memory, 65535), 7, 2), 'out of bounds')
        throws(lambda: call('fill', pointer(memory, 0), 7, -1), 'out of bounds')
        assert bytes(target.read(store)) == before, 'failed fill changed memory'
    for memory in (3, 0xffffffff):
        throws(lambda: call('fill', pointer(memory, 0), 7, 0), 'memory failure 7')
    exports['memory0'].write(store, pattern, 100)
    for memory in range(3):
        call('copy_from_frame', pointer(memory, 1000), 100, len(pattern))
        assert bytes(exports[f'memory{memory}'].read(store, 1000, 1004)) == pattern
    for memory in range(3):
        frame = exports['memory0']
        frame.write(store, bytes([90] * 6), 1100)
        call('copy_to_frame', 1101, pointer(memory, 1000), 4)
        assert bytes(frame.read(store, 1100, 1106)) == bytes([90, 0, 127, 128, 255, 90])
    for memory in (3, 0xffffffff):
        throws(lambda: call('copy_to_frame', 1101, pointer(memory, 1000), 4), 'memory failure 7')
    call('copy_to_frame', 65536, pointer(2, 65536), 0)
    call('copy_from_frame', pointer(2, 65536), 65536, 0)
    for memory in (3, 0xffffffff):
        throws(lambda: call('copy_from_frame', pointer(memory, 1000), 100, 4), 'memory failure 7')
    throws(lambda: call('copy_from_frame', pointer(2, 1000), 65535, 2), 'out of bounds')
    assert bytes(exports['memory2'].read(store, 1000, 1004)) == pattern
    call('store8', pointer(2, 65535), 90)
    throws(lambda: call('copy_from_frame', pointer(2, 65535), 100, 2), 'out of bounds')
    assert call('load8u', pointer(2, 65535)) == 90
    for memory in range(3):
        call('store32', pointer(memory, 2000), 17)
        call('store32off', pointer(memory, 2000), 0xffffffff)
        assert call('load32u', pointer(memory, 2000)) == 17
        assert call('load32off', pointer(memory, 2000)) == 0xffffffff
    throws(lambda: call('load32huge', pointer(0, 0)), 'out of bounds')
    throws(lambda: call('load32off', pointer(3, 2000)), 'memory failure 7')
    throws(lambda: call('load32off', pointer(2, 65532)), 'out of bounds')
    for memory in range(3):
        exports[f'memory{memory}'].write(store, bytes([memory, 0, 127, 255]), 3000)
    for source in range(3):
        for destination in range(3):
            call('copy', pointer(destination, 4000), pointer(source, 3000), 4)
            assert bytes(exports[f'memory{destination}'].read(store, 4000, 4004)) == bytes([source, 0, 127, 255])
    exports['memory1'].write(store, bytes([1, 2, 3, 4, 5]), 5000)
    call('copy', pointer(1, 5001), pointer(1, 5000), 4)
    assert bytes(exports['memory1'].read(store, 5000, 5005)) == bytes([1, 1, 2, 3, 4])
    call('copy', pointer(1, 5000), pointer(1, 5001), 4)
    assert bytes(exports['memory1'].read(store, 5000, 5004)) == bytes([1, 2, 3, 4])
    throws(lambda: call('copy', pointer(3, 4000), pointer(0, 3000), 4), 'memory failure 7')
    throws(lambda: call('copy', pointer(0, 4000), pointer(3, 3000), 4), 'memory failure 7')
    throws(lambda: call('copy', pointer(2, 4000), pointer(0, 65535), 2), 'out of bounds')
    assert bytes(exports['memory2'].read(store, 4000, 4004)) == bytes([2, 0, 127, 255])
    assert call('reserve1', 65536 - 65) == 65
    assert call('reserve1', 1) == 65536
    assert size(1) == 131072 and size(2) == 65536
    assert call('load64', pointer(1, 3)) == -(1 << 63) + 1
    assert call('reserve2', 131072) == 65
    assert size(2) == 196608 and size(1) == 131072
    assert call('load64', pointer(2, 3)) == -(1 << 63) + 2
    call('restore', 1, 65)
    assert call('top', 1) == 65
    throws(lambda: call('reserve1', -1), 'memory failure 6')
    assert call('top', 1) == 65 and size(1) == 131072
    throws(lambda: call('restore', 1, 0), 'memory failure 7')
    throws(lambda: call('restore', 2, size(2) + 1), 'memory failure 7')
    for memory in (0, 3, -1):
        throws(lambda: call('reserve', memory, 1), 'memory failure 7')
        throws(lambda: call('top', memory), 'memory failure 7')
    throws(lambda: call('load64', pointer(3, 1)), 'memory failure 7')
    throws(lambda: call('load64', pointer(2, size(2))), 'out of bounds')

    store2, limited = instance(sys.argv[2])
    assert limited['reserve1'](store2, 65535) == 1
    limited['store64'](store2, pointer(1, 3), 12345)
    throws(lambda: limited['reserve1'](store2, 1), 'memory failure 6')
    assert limited['top'](store2, 1) == 65536
    assert limited['memory1'].data_len(store2) == 65536
    assert limited['memory2'].data_len(store2) == 65536
    assert limited['load64'](store2, pointer(1, 3)) == 12345
    print('Wasmtime data-memory runtime checks passed')


if __name__ == '__main__':
    main()
