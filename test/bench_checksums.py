#!/usr/bin/env python3
"""Check complete typed results, including failures; no timing assertions."""
import json
import math
import pathlib
import struct
import subprocess
import sys
import tempfile

exe = pathlib.Path(sys.argv[1]).resolve()
checks = 0
with tempfile.TemporaryDirectory(prefix='goose-bench-checksums-') as directory:
    folder = pathlib.Path(directory)
    source = folder / 'entry.goose'
    for kind, width, fmt in [('f32', 32, '>f'), ('f64', 64, '>d')]:
        for case, expression in [('nan', 'zero / zero'), ('inf', 'one / zero'), ('finite', '1.5')]:
            source.write_text(f'var zero: {kind} = 0.0;\nvar one: {kind} = 1.0;\n'
                              f'bench "components" fn components() -> {kind}, i64, bool, {kind}, u64 {{\n'
                              f'    return {expression}, 42, true, 1.5, 18446744073709551615;\n}}\n')
            artifact = folder / f'{kind}-{case}.json'
            result = subprocess.run([str(exe), 'bench', str(source), '--temperature', 'off',
                                     '--samples', '5', '--warmups', '1', '--json', str(artifact)],
                                    capture_output=True, text=True, timeout=120)
            assert result.returncode == (0 if case == 'finite' else 1), (kind, case, result.stdout, result.stderr)
            report = json.loads(artifact.read_text())
            row, = report['results']
            assert report['status'] == row['status'] == ('ok' if case == 'finite' else 'failed')
            assert len(row['attempts']) == (6 if case == 'finite' else 1)
            for attempt in row['attempts']:
                components = attempt['checksum']['components']
                assert [c['type'] for c in components] == [kind, 'i64', 'bool', kind, 'u64'], components
                assert [components[i]['value'] for i in (1, 2, 4)] == ['42', True, '18446744073709551615']
                for index in (0, 3):
                    bits = components[index]['value']
                    assert bits.startswith('0x') and len(bits) == 2 + width // 4
                    value, = struct.unpack(fmt, bytes.fromhex(bits[2:]))
                    if index == 3 or case == 'finite':
                        assert value == 1.5
                    elif case == 'nan':
                        assert math.isnan(value)
                    else:
                        assert math.isinf(value)
                if case != 'finite':
                    assert attempt['status'] == 'failed' and attempt['error']['code'] == 'checksum'
                    assert 'nonfinite benchmark checksum' in attempt['error']['message']
            checks += 1
print(f'benchmark checksums: {checks} complete-result cases passed')
