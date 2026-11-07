"""Synthetic compiler-private place contracts under Wasmtime, without timing."""
from pathlib import Path
import struct
import sys
import wasmtime


def main():
    config = wasmtime.Config(); config.wasm_multi_memory = True
    engine = wasmtime.Engine(config); store = wasmtime.Store(engine)
    module = wasmtime.Module(engine, Path(sys.argv[1]).read_bytes())

    def fail(code, offset, length, line):
        raise RuntimeError(f'place failure {code}')

    x = wasmtime.Instance(store, module, [wasmtime.Func(store, module.imports[0].type, fail)]).exports(store)
    ptr = lambda memory, offset: (memory << 32) | offset
    call = lambda name, *args: x[name](store, *args)

    def throws(action, reason):
        try:
            action()
        except Exception as error:
            assert reason in str(error), error
        else:
            raise AssertionError(f'expected {reason}')

    for value in (0, 1, 16, 0xffffffff):
        argument = value if value < 1 << 31 else value - (1 << 32)
        assert call('pack0', argument) == value
        assert call('pack2', argument) == ptr(2, value)
    assert call('packconstant') == ptr(2, 32)
    assert call('pack2off', 16) == ptr(2, 23)
    assert call('pack2bounded', 16) == ptr(2, 23)
    assert call('packedoff', ptr(1, 16)) == ptr(1, 23)
    assert call('knownoff', ptr(2, 16)) == 23
    assert call('thin0', ptr(0, 16)) == 23
    throws(lambda: call('pack2off', -2), 'place failure 11')
    throws(lambda: call('packedoff', ptr(1, 0xfffffffe)), 'place failure 11')
    throws(lambda: call('knownoff', ptr(2, 0xfffffffe)), 'place failure 11')
    throws(lambda: call('thin0', ptr(1, 16)), 'place failure 7')
    memories = [x[f'memory{i}'] for i in range(3)]
    memories[2].write(store, struct.pack('<II', 32, 3), 19)
    for mode in ('thin', 'known', 'dynamic'):
        address = 16 if mode == 'thin' else ptr(2, 16)
        assert call(mode + 'cap', address) == 32
        assert call(mode + 'len', address) == 3
        for index in range(3):
            actual = call(mode + 'element', address, index)
            assert actual == ptr(2, 27 + index), f'{mode} element lost its memory identity: {actual}'
        call(mode + 'store', address, 2)
        assert bytes(memories[2].read(store, 23, 27)) == struct.pack('<I', 2)
        memories[2].write(store, struct.pack('<I', 3), 23)
    for name, destination, source in [('copy00', 0, 0), ('copy20', 2, 0), ('copy02', 0, 2),
                                      ('copy0u', 0, 1), ('copyu0', 1, 0), ('copy2u', 2, 1),
                                      ('copyu2', 1, 2), ('copyuu', 1, 2), ('copyuu', 2, 2)]:
        for i, memory in enumerate(memories): memory.write(store, bytes([40 + i]) * 64, 256)
        memories[source].write(store, bytes(range(1, 9)), 256)
        before = [bytearray(memory.read(store)) for memory in memories]
        expected = [bytearray(value) for value in before]
        offset = 258 if destination == source else 280
        expected[destination][offset:offset + 8] = before[source][256:264]
        call(name, ptr(destination, offset), ptr(source, 256), 8)
        for i, memory in enumerate(memories): assert memory.read(store) == expected[i], name
    memories[2].write(store, bytes([11, 12, 13, 14]), 32)
    call('copyconstant', ptr(1, 400))
    assert bytes(memories[1].read(store, 400, 404)) == bytes([11, 12, 13, 14])
    for destination, source, reason in [(ptr(3, 256), ptr(1, 256), 'place failure 7'),
                                        (ptr(1, 256), ptr(3, 256), 'place failure 7'),
                                        (ptr(1, 65534), ptr(2, 256), 'out of bounds'),
                                        (ptr(1, 256), ptr(2, 65534), 'out of bounds')]:
        before = [memory.read(store) for memory in memories]
        throws(lambda: call('copyuu', destination, source, 8), reason)
        for i, memory in enumerate(memories): assert memory.read(store) == before[i], 'failed copy changed memory'
    print('array places: PASS')


if __name__ == '__main__':
    main()
