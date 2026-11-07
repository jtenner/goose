"""Fixed-enum controls and bounded constructor footprint checks."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def check_modules(run, node, validator, wasmtime_python, out):
    count = 0

    def control(name, text, reason, source, line):
        nonlocal count
        wat = out / (name + '.wat'); wat.write_text(text)
        module = wat.with_suffix('.wasm')
        run([validator, 'parse', wat, '-o', module])
        run([validator, 'validate', module])
        engines = [[node, ROOT / 'scripts/run_wasm.mjs', module]]
        if wasmtime_python:
            engines.append([wasmtime_python, ROOT / 'test/wasmtime_host.py', module])
        for command in engines:
            result = run(command, ok=False)
            assert result.returncode and reason.encode() in result.stderr, (name, result.stderr)
            assert f'{source}:{line}'.encode() in result.stderr, (name, 'wrong failure site', result.stderr)
            assert result.stdout == b'', (name, 'control ran past the expected failure')
            count += 1

    def replace(text, pattern, replacement, expected=1):
        assert len(re.findall(pattern, text)) == expected, (pattern, 'control site missing or ambiguous')
        return re.sub(pattern, replacement, text)

    source = ROOT / 'test/wasm/wasm_enum_control.goose'
    lines = source.read_text().splitlines()
    line = lambda needle: next(i for i, text in enumerate(lines, 1) if needle in text)
    for opt in (0, 2):
        text = run([validator, 'print', out / f'wasm_enum_control-O{opt}.wasm']).stdout.decode()
        broken = replace(text, r'i32\.const 1(?=\s+i32\.add\s+i64\.extend_i32_u)', 'i32.const 0')
        control(f'enum-wrong-payload-O{opt}', broken, 'assert failed', source, line('assert(p.x'))
        pattern = (r'i32\.const 7(?=\s+local\.set \d+\s+local\.get \d+\s+i32\.wrap_i64'
                   r'\s+local\.get \d+\s+i32\.wrap_i64\s+local\.get \d+\s+memory\.copy)')
        broken = replace(text, pattern, 'i32.const 6')
        control(f'enum-short-copy-O{opt}', broken, 'assert failed', source, line('assert(p.z'))
        broken = replace(text, r'i64\.load8_u offset=4(?=\s|$)', 'i64.load offset=4 align=1')
        control(f'enum-wide-field-O{opt}', broken, 'assert failed', source, line('assert(p.y'))
        broken = replace(text, r'i64\.const 0(?=\s+i64\.store8(?:\s|$))', 'i64.const 2')
        control(f'enum-invalid-tag-O{opt}', broken, 'invalid fixed enum tag', source, line('match original'))
        wildcard = ROOT / 'test/wasm/wasm_enum_wildcard.goose'
        text = run([validator, 'print', out / f'wasm_enum_wildcard-O{opt}.wasm']).stdout.decode()
        broken = replace(text, r'i64\.const 0(?=\s+i64\.store8(?:\s|$))', 'i64.const 2')
        control(f'enum-invalid-wildcard-O{opt}', broken, 'invalid fixed enum tag', wildcard, 3)
        tags = ROOT / 'test/wasm/wasm_enum_tags.goose'
        text = run([validator, 'print', out / f'wasm_enum_tags-O{opt}.wasm']).stdout.decode()
        broken = replace(text, r'i64\.const 256\s+i64\.store16 align=1', 'i64.const 256\n      i64.store8')
        badline = next(i for i, text in enumerate(tags.read_text().splitlines(), 1)
                       if '_ => assert(false)' in text and i > 6)
        control(f'enum-short-tag-O{opt}', broken, 'assert failed', tags, badline)
        text = run([validator, 'print', out / f'wasm_enum_hidden-O{opt}.wasm']).stdout.decode()
        bounce = [line for line in text.splitlines() if re.search(r'\(func \$bounce\.', line)]
        assert len(bounce) == 1 and '(param i64 i64) (result i64)' in bounce[0], bounce
        count += 1
    return count


def check_footprint(run, exe, node, validator, wasmtime_python, out, local_counts):
    observed = []
    for length in (32, 256):
        source = out / f'enum-local-count-{length}.goose'
        values = ', '.join(str(i % 251) for i in range(length))
        source.write_text('enum E { A { items: i64[..1024], after: i64 }, B }\n'
                          'fn main() { var e: E = E.A { items: [' + values + '], after: 99 }; '
                          f'match e {{ A p => print(p.items.len, ",", p.items[{length - 1}], ",", p.after), '
                          'B => assert(false) } }\n')
        expected = f'{length},{(length - 1) % 251},99\n'.encode()
        for opt in (0, 2):
            module = out / f'enum-local-count-{length}-O{opt}.wasm'
            run([exe, f'-O{opt}', '--target', 'wasm', '-o', module, source])
            counts = local_counts(module.read_bytes())
            assert max(counts) <= 96, 'enum constructor scratch grew with literal length'
            observed.append(counts)
            run([validator, 'validate', module])
            assert run([node, ROOT / 'scripts/run_wasm.mjs', module]).stdout == expected
            if wasmtime_python:
                assert run([wasmtime_python, ROOT / 'test/wasmtime_host.py', module]).stdout == expected
    assert all(counts == observed[0] for counts in observed), observed
    return len(observed)
