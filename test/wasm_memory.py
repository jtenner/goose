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

    def call(name, *args):
        return exports[name](store, *args)

    def pointer(memory, offset):
        return (memory << 32) | offset

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
