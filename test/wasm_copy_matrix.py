#!/usr/bin/env python3
"""Functional checks for the bounded two-identity copy dispatcher."""
import sys
from wasm_memory import instance, throws
store, x = instance(sys.argv[1])
count = 65
pointer = lambda memory, offset: (memory << 32) | offset
for i in range(count):
    x[f'memory{i}'].write(store, bytes([128, 1]), 500)
    assert x['read_prefix'](store, pointer(i, 500)) == [128, 2]
throws(lambda: x['read_prefix'](store, pointer(count, 500)), 'memory failure 7')
for i in range(count):
    x[f'memory{i}'].write(store, bytes([i, 0, 127, 255]), 100)
for source in range(count):
    for destination in range(count):
        x['copy'](store, pointer(destination, 200), pointer(source, 100), 4)
        assert bytes(x[f'memory{destination}'].read(store, 200, 204)) == bytes([source, 0, 127, 255])
frame = x['memory0']
for source in range(count):
    frame.write(store, bytes([91] * 6), 299)
    x['copy_to_frame'](store, 300, pointer(source, 100), 4)
    assert bytes(frame.read(store, 299, 305)) == bytes([91, source, 0, 127, 255, 91])
x['copy_to_frame'](store, 65536, pointer(64, 65536), 0)
frame.write(store, bytes([91] * 6), 299)
for invalid in (count, 0xffffffff):
    throws(lambda: x['copy_to_frame'](store, 300, pointer(invalid, 100), 4), 'memory failure 7')
    assert bytes(frame.read(store, 299, 305)) == bytes([91] * 6)
throws(lambda: x['copy_to_frame'](store, 300, pointer(64, 65535), 2), 'out of bounds')
assert bytes(frame.read(store, 299, 305)) == bytes([91] * 6)
frame.write(store, bytes([92]), 65535)
throws(lambda: x['copy_to_frame'](store, 65535, pointer(64, 100), 2), 'out of bounds')
assert bytes(frame.read(store, 65535, 65536)) == bytes([92])
frame.write(store, bytes([1, 2, 3, 4, 5]), 400)
x['copy_to_frame'](store, 401, pointer(0, 400), 4)
assert bytes(frame.read(store, 400, 405)) == bytes([1, 1, 2, 3, 4])
x['copy'](store, pointer(64, 65536), pointer(63, 65536), 0)
throws(lambda: x['copy'](store, pointer(count, 200), pointer(0, 100), 4), 'memory failure 7')
throws(lambda: x['copy'](store, pointer(0, 200), pointer(count, 100), 4), 'memory failure 7')
throws(lambda: x['copy'](store, pointer(64, 200), pointer(0, 65535), 2), 'out of bounds')
assert bytes(x['memory64'].read(store, 200, 204)) == bytes([64, 0, 127, 255])
x['store8'](store, pointer(64, 65535), 90)
throws(lambda: x['copy'](store, pointer(64, 65535), pointer(0, 100), 2), 'out of bounds')
assert x['load8u'](store, pointer(64, 65535)) == 90
print('Wasmtime 65-memory copy matrix passed')
