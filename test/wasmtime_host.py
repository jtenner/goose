#!/usr/bin/env python3
"""Test adapter for the Goose scalar ABI using the optional wasmtime package."""
import math
from pathlib import Path
import struct
import sys
import wasmtime


def format_float(value, width):
    if math.isnan(value):
        return 'nan'
    if math.isinf(value):
        return '-inf' if value < 0 else 'inf'
    sign = '-' if math.copysign(1, value) < 0 else ''
    value = abs(value)
    if value == 0:
        return sign + '0.0'
    decimal = repr(value)
    if width == 32:
        for n in range(1, 10):
            candidate = format(value, f'.{n}g')
            try:
                same = struct.unpack('<f', struct.pack('<f', float(candidate)))[0] == value
            except OverflowError:
                same = False
            if same:
                decimal = candidate
                break
    parts = decimal.split('e')
    mantissa = parts[0]
    exponent = int(parts[1]) if len(parts) > 1 else 0
    k = (mantissa.index('.') if '.' in mantissa else len(mantissa)) + exponent
    digits = mantissa.replace('.', '')
    while digits.startswith('0'):
        digits = digits[1:]
        k -= 1
    digits = digits.rstrip('0')
    x = k - 1
    if x < -4 or x >= max(len(digits), 15):
        fraction = '.' + digits[1:] if len(digits) > 1 else ''
        return f'{sign}{digits[0]}{fraction}e{"-" if x < 0 else "+"}{abs(x):02d}'
    if x < 0:
        return sign + '0.' + '0' * (-x - 1) + digits
    if len(digits) <= k:
        return sign + digits.ljust(k, '0') + '.0'
    return sign + digits[:k] + '.' + digits[k:]


class GuestExit(Exception):
    def __init__(self, code):
        self.code = code


def execute(path):
    config = wasmtime.Config()
    config.wasm_multi_memory = True
    config.wasm_exceptions = True
    engine = wasmtime.Engine(config)
    module = wasmtime.Module.from_file(engine, path)
    store = wasmtime.Store(engine)
    linker = wasmtime.Linker(engine)
    pending = {}
    serial = 0

    def read(caller, offset, length):
        offset &= 0xffffffff
        length &= 0xffffffff
        memory = caller.get('memory')
        size = memory.data_len(caller)
        if offset > size or length > size - offset:
            raise RuntimeError('host byte range is outside Memory 0')
        return bytes(memory.read(caller, offset, offset + length))

    def dispatch(name, caller, args):
        nonlocal serial
        if name == 'print_begin_v1':
            serial += 1
            pending[serial] = []
            return serial
        if name == 'print_int_v1':
            token, value, unsigned = args
            if unsigned:
                value &= (1 << 64) - 1
            pending[token].append(str(value).encode())
        elif name == 'print_float_v1':
            token, value, width = args
            pending[token].append(format_float(value, width).encode())
        elif name == 'print_bool_v1':
            token, value = args
            pending[token].append(b'true' if value else b'false')
        elif name == 'print_bytes_v1':
            token, offset, length = args
            pending[token].append(read(caller, offset, length))
        elif name == 'print_end_v1':
            sys.stdout.buffer.write(b''.join(pending.pop(args[0])) + b'\n')
        elif name == 'fail_v1':
            code, offset, length, line = args
            reason = {1: 'assert failed', 2: 'division by zero', 3: 'integer division overflow',
                      4: 'null reference', 5: 'out of memory growing frame storage'}[code]
            source = read(caller, offset, length).decode()
            raise RuntimeError(f'goose runtime error: {reason}' + (f' at {source}:{line}' if source else ''))
        elif name == 'exit_v1':
            raise GuestExit(args[0] & 255)
        elif name == 'fmod_v1':
            a, b = args
            try:
                return math.fmod(a, b)
            except ValueError:
                return math.nan
        elif name == 'float_to_int_v1':
            value = args[0]
            result = math.trunc(value) & ((1 << 64) - 1) if math.isfinite(value) else 0
            return result if result < 1 << 63 else result - (1 << 64)
        else:
            raise RuntimeError(f'unsupported test import: {name}')
        return None

    for imported in module.imports:
        if imported.module != 'goose' or not isinstance(imported.type, wasmtime.FuncType):
            raise RuntimeError(f'unsupported test import: {imported.module}.{imported.name}')
        def callback(caller, *args, name=imported.name):
            return dispatch(name, caller, args)
        linker.define_func('goose', imported.name, imported.type, callback, access_caller=True)
    instance = linker.instantiate(store, module)
    instance.exports(store)['_start'](store)
    assert not pending, 'unfinished print buffers remain'


if __name__ == '__main__':
    try:
        execute(str(Path(sys.argv[1])))
    except GuestExit as error:
        sys.exit(error.code)
    except Exception as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
