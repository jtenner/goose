"""Live-owner and damaged-copy checks for fixed aggregate iteration."""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]


def check_modules(run, node, validator, wasmtime_python, out):
    count = 0

    def module(name, text):
        wat = out / ('iteration-' + name + '.wat'); wat.write_text(text)
        result = wat.with_suffix('.wasm')
        run([validator, 'parse', wat, '-o', result]); run([validator, 'validate', result])
        return result

    def failure(name, wasm, source, assertion, stdout=b''):
        line = next(i for i, text in enumerate(source.read_text().splitlines(), 1) if assertion in text)
        engines = [[node, ROOT / 'scripts/run_wasm.mjs', wasm]]
        if wasmtime_python:
            engines.append([wasmtime_python, ROOT / 'test/wasmtime_host.py', wasm])
        for command in engines:
            result = run(command, ok=False)
            assert result.returncode and b'assert failed' in result.stderr, (name, result.stderr)
            assert f'{source}:{line}'.encode() in result.stderr, (name, 'wrong assertion', result.stderr)
            assert result.stdout == stdout, (name, 'wrong failure ordering', result.stdout)
        return len(engines)

    def owner(wasm, mode, reason=None, stdout=b''):
        result = run([node, ROOT / 'test/wasm_iteration_owner.mjs', wasm, mode], ok=reason is None)
        if reason is not None:
            assert result.returncode and reason in result.stderr, result.stderr
        else:
            assert not result.stderr
        assert result.stdout == stdout, result.stdout

    for opt in (0, 2):
        stem = f'O{opt}'
        texts = {}
        owners = {}
        for name, mode in [('control', 'copy'), ('checkpoint', 'cleanup'), ('zero_control', 'zero')]:
            base = f'wasm_aggregate_iteration_{name}'
            text = run([validator, 'print', out / f'{base}-{stem}.wasm']).stdout.decode()
            assert 'test_stack_top_0' not in text
            memories = 3 if name == 'checkpoint' else 1
            exports = ''.join(f'  (export "test_stack_top_{i}" (global {i}))\n' for i in range(memories))
            derived = text[:text.rfind(')')] + exports + ')\n'
            wasm = module(f'{name}-{stem}-owner', derived)
            owner(wasm, mode, stdout=(ROOT / 'test/expected' / f'{base}.out').read_bytes())
            texts[name], owners[name] = text, derived
            count += 1
        text = texts['control']; source = ROOT / 'test/wasm/wasm_aggregate_iteration_control.goose'
        pattern = (r'i32.const 7(?=\n\s+local.set \d+\n\s+local.get \d+\n\s+i32.wrap_i64'
                   r'\n\s+local.get \d+\n\s+i32.wrap_i64\n\s+local.get \d+\n\s+memory.copy)')
        assert len(re.findall(pattern, text)) == 1, 'loop-copy length is not unique'
        short = module('short-' + stem, re.sub(pattern, 'i32.const 6', text))
        count += failure('short', short, source, 'assert(s.tail')
        stride_pattern = r'i64.const 7(?=\s+i64.mul)'
        assert len(re.findall(stride_pattern, text)) == 2
        stride = module('stride-' + stem, re.sub(stride_pattern, 'i64.const 8', text, count=1))
        count += failure('stride', stride, source, 'assert(s.mark', b'iteration\n')
        assert len(re.findall(r'i32.const 14(?=\s)', text)) == 4
        alias = module('alias-' + stem, re.sub(r'i32.const 14(?=\s)', 'i32.const 0', text))
        count += failure('alias', alias, source, 'assert(s.n')
        long = module('long-' + stem, re.sub(pattern, 'i32.const 8', owners['control']))
        owner(long, 'copy', b'iteration copy crossed its planned owner image'); count += 1
        guard = (r'(loop[^\n]*\n)(\s+local.get \d+\n\s+local.get \d+\n\s+i64.load8_u'
                 r'\n\s+i64.ge_u\n\s+br_if [^\n]+\n)(.*?memory.copy\n)')
        assert len(re.findall(guard, owners['zero_control'], re.S)) == 1
        eager = module('eager-' + stem, re.sub(guard, lambda m: m[1] + m[3] + m[2],
                                              owners['zero_control'], count=1, flags=re.S))
        owner(eager, 'zero', b'zero-trip iteration copied an element'); count += 1
        cleanup = owners['checkpoint']; start = cleanup.index('(func $main.0')
        end = cleanup.index('\n  (func ', start); main = cleanup[start:end]
        assert 'global.set 2' in main
        broken = module('cleanup-' + stem, cleanup[:start] + main.replace('global.set 2', 'drop', 1) + cleanup[end:])
        owner(broken, 'cleanup', b'iteration body data top was not restored at its completion', b'inner\n')
        count += 1
        text = run([validator, 'print', out / f'wasm_aggregate_iteration_refs_packed-{stem}.wasm']).stdout.decode()
        pattern9 = pattern.replace('const 7', 'const 9')
        assert len(re.findall(pattern9, text)) == 1
        at = re.search(pattern9, text).start(); copy = text.index('memory.copy', at)
        wrong = module('memory-' + stem, text[:copy] + text[copy:].replace('memory.copy', 'memory.copy 0 1', 1))
        count += failure('memory', wrong, ROOT / 'test/wasm/wasm_aggregate_iteration_refs_packed.goose',
                         'assert(s.value .==')
    return count


def check_limits(run, exe, out):
    source = out / 'iteration-frame-limit.goose'
    source.write_text('struct S { bytes: u8[2147483648] }\n'
                      'fn main() { var a: S[..1] = []; for s in a { assert(s.bytes[0] == 0); } print("limit"); }\n')
    for opt in (0, 2):
        prefix = out / f'iteration-frame-limit-O{opt}'
        run([exe, f'-O{opt}', '--standalone', '-o', prefix.with_suffix('.c'), source])
        wasm = prefix.with_suffix('.wasm')
        result = run([exe, f'-O{opt}', '--target', 'wasm', '-o', wasm, source], ok=False)
        assert result.returncode and b'wasm target:' in result.stderr and b'frame exceeds memory32' in result.stderr
        assert not wasm.exists()
    return 2


def check_footprint(run, exe, cc, node, validator, wasmtime_python, out):
    rows = []
    for kind, values in [('length', (0, 1, 32, 256)), ('capacity', (32, 65536))]:
        for value in values:
            source = out / f'iteration-{kind}-{value}.goose'
            elements = ', '.join(['S { n: 1 }'] * value) if kind == 'length' else 'S { n: 1 }'
            extent = str(value) if kind == 'length' else '..' + str(value)
            length = value if kind == 'length' else 1
            source.write_text('struct S { n: i64 }\n' +
                              f'var values: S[{extent}] = [' + elements + '];\n' +
                              'fn main() { var total: i64 = 0; for s in values { total += s.n; } ' +
                              f'assert(total == {length}); print("footprint"); }}\n')
            for opt in (0, 2):
                prefix = out / f'iteration-{kind}-{value}-O{opt}'
                c, native, wasm = (prefix.with_suffix(ext) for ext in ('.c', '.native', '.wasm'))
                run([exe, f'-O{opt}', '--standalone', '-o', c, source])
                run([cc, '-O0', c, '-pthread', '-lm', '-ldl', '-o', native])
                assert run([native]).stdout == b'footprint\n'
                run([exe, f'-O{opt}', '--target', 'wasm', '-o', wasm, source])
                run([validator, 'validate', wasm])
                engines = [[node, ROOT / 'scripts/run_wasm.mjs', wasm]]
                if wasmtime_python:
                    engines.append([wasmtime_python, ROOT / 'test/wasmtime_host.py', wasm])
                for command in engines:
                    result = run(command); assert result.stdout == b'footprint\n' and not result.stderr
                text = run([validator, 'print', wasm]).stdout.decode()
                start = text.index('(func $main.0'); main = text[start:text.index('\n  (func ', start)]
                locals_ = next(line for line in main.splitlines() if line.strip().startswith('(local '))
                assert re.search(r'i32.const 8\s+call \$goose.reserve_frame', main)
                loop = re.search(r'\n\s+loop\b', main); assert loop
                assert 'call $goose.reserve_frame' not in main[loop.start():]
                assert main.count('memory.copy') == 1
                rows.append({'kind': kind, 'value': value, 'opt': opt, 'bytes': wasm.stat().st_size,
                             'main_locals': len(re.findall(r'\b(?:i32|i64|f32|f64)\b', locals_)),
                             'binder_frame_bytes': 8, 'loop_copy_sites': 1})
    assert len({row['main_locals'] for row in rows}) == 1, rows
    sparse = [row['bytes'] for row in rows if row['kind'] == 'capacity']
    assert max(sparse) < 16384 and max(sparse) - min(sparse) < 128, sparse
    (out / 'iteration-footprint.json').write_text(json.dumps(rows, indent=2) + '\n')
    return len(rows)
