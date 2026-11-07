"""Full stored-image replacement and valid damaged-copy controls."""
from pathlib import Path
import re
from wasm_data_iteration_checks import function_span
ROOT = Path(__file__).resolve().parents[1]


def check_images(run, node, validator, out):
    count = 0
    for opt in (0, 2):
        text = run([validator, 'print', out / f'wasm_fixed_assignment_image-O{opt}.wasm']).stdout.decode()
        a, z = function_span(text, 'main'); body = text[a:z]
        assert re.findall(r'i32.const (\d+)\s+call \$goose.reserve_frame', body) == ['27']
        pattern = r'i32.const 9(?=\s+memory.copy(?: 0 0)?\s)'
        assert len(re.findall(pattern, body)) == 2
        exports = '  (export "test_stack_top_0" (global 0))\n'
        def emit(name, value):
            value = value[:value.rfind(')')] + exports + ')\n'
            wat = out / f'fixed-assignment-{name}-O{opt}.wat'; wat.write_text(value)
            wasm = wat.with_suffix('.wasm')
            run([validator, 'parse', wat, '-o', wasm]); run([validator, 'validate', wasm])
            return wasm
        healthy = emit('image', text)
        result = run([node, ROOT / 'test/wasm_fixed_assignment_image.mjs', healthy])
        assert result.stdout == b'seed\ncopied\nemptied\n' and not result.stderr
        count += 1
        damaged = [('short', re.sub(pattern, 'i32.const 2', body, count=1)),
                   ('long', re.sub(pattern, 'i32.const 10', body, count=1))]
        omitted, n = re.subn(r'(?m)^(\s*)memory.copy(?: 0 0)?\s*$',
                            r'\1drop\n\1drop\n\1drop', body, count=1)
        assert n == 1; damaged.append(('omitted', omitted))
        for name, changed in damaged:
            wasm = emit(name, text[:a] + changed + text[z:])
            result = run([node, ROOT / 'test/wasm_fixed_assignment_image.mjs', wasm], ok=False)
            assert result.returncode == 1 and b'exact fixed assignment image differs' in result.stderr, (name, result.stderr)
            assert result.stdout == b'seed\n', (name, result.stdout)
            count += 1
    return count


def check_guards(run, exe, out, node, validator, wasmtime_python):
    cases = [
        ('constructor', 'struct S { n: i64 }\n'
         'fn main() { var a: S = S { n: 1 }; a = S { n: 2 }; print(a.n); }\n',
         b'2\n'),
        ('enum-constant', 'enum E { A { n: i64 }, B }\n'
         'fn main() { var a: E = E.A { n: 1 }; a = E.B; match a { B => print(0), _ => assert(false) } }\n',
         b'0\n'),
    ]
    count = 0
    for name, text, expected in cases:
        source = out / ('fixed-assignment-' + name + '-guard.goose'); source.write_text(text)
        for opt in (0, 2):
            prefix = out / f'fixed-assignment-{name}-guard-O{opt}'
            run([exe, f'-O{opt}', '--standalone', '-o', prefix.with_suffix('.c'), source])
            module = prefix.with_suffix('.wasm'); module.unlink(missing_ok=True)
            run([exe, f'-O{opt}', '--target', 'wasm', '-o', module, source])
            run([validator, 'validate', module])
            commands = [[node, ROOT / 'scripts/run_wasm.mjs', module]]
            if wasmtime_python:
                commands.append([wasmtime_python, ROOT / 'test/wasmtime_host.py', module])
            for command in commands:
                result = run(command)
                assert result.stdout == expected and not result.stderr, (name, result.stdout, result.stderr)
                count += 1
    source = out / 'fixed-assignment-lifetime-guard.goose'
    source.write_text('struct S { value: i64& }\n'
                      'fn main() { var old: i64[] = [1]; var holder: S = S { value: old[0] }; '
                      '{ var inner: i64[] = [7]; var source: S = S { value: inner[0] }; holder = source; } '
                      'print(holder.value); }\n')
    result = run([exe, '--check', source], ok=False)
    assert result.returncode == 1 and (
        b'storing a reference rooted at inner, which does not outlive the destination') in result.stderr, result.stderr
    return count + 1
