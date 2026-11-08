"""Array construction atomicity, live owner restoration and failure controls."""
from pathlib import Path
import re
from wasm_data_iteration_checks import function_span
ROOT = Path(__file__).resolve().parents[1]


def check_owners(run, node, validator, out):
    count = 0
    for opt in (0, 2):
        for name in ('loop', 'early_owner', 'nested_owner'):
            module = out / f'wasm_array_constructor_{name}-O{opt}.wasm'
            text = run([validator, 'print', module]).stdout.decode()
            def emit(suffix, value):
                value = value[:value.rfind(')')] + '  (export "test_stack_top_0" (global 0))\n)\n'
                wat = out / f'array-constructor-{name}-{suffix}-O{opt}.wat'
                wasm = wat.with_suffix('.wasm')
                wat.write_text(value)
                run([validator, 'parse', wat, '-o', wasm]); run([validator, 'validate', wasm])
                return wasm
            healthy = emit('owner', text)
            actual = run([node, ROOT / 'test/wasm_array_constructor_owner.mjs', healthy, name])
            expected = (ROOT / 'test/expected' / f'wasm_array_constructor_{name}.out').read_bytes()
            assert actual.stdout == expected and not actual.stderr
            count += 1
            if name == 'loop':
                a, z = function_span(text, 'main')
                body, n = re.subn(r'(?m)^(\s*)global.set (?:0|\$[^\s]+)\s*$',
                                  r'\1drop', text[a:z], count=1)
                assert n == 1
                damaged = emit('missing-restore', text[:a] + body + text[z:])
                result = run([node, ROOT / 'test/wasm_array_constructor_owner.mjs', damaged, name], ok=False)
                assert result.returncode == 1 and b'array constructor temporary live frame top differs' in result.stderr
                count += 1
    return count


def check_failures(run, exe, cc, node, validator, out):
    cases = [
        ('failure', 'var target:i64[2]=[1,2];var divisor:i64=0;\n'
         'fn main(){print("before");target=[9,8/divisor];print("after");}\n',
         b'division by zero', ''),
        ('target', 'struct H{a:i64[2]}\nvar index:i64=1;\n'
         'recursive fn effect()->i64{print("rhs");return 9;}\n'
         'fn main(){var rows:H[]=[H{a:[1,2]}];print("before");'
         'rows[index].a=[effect(),10];print("after");}\n',
         b'index 1 out of bounds (length 1)', 'bounds'),
    ]
    count = 0
    for name, source, reason, mode in cases:
        path = out / f'array-constructor-{name}.goose'; path.write_text(source)
        for opt in (0, 2):
            prefix = out / f'array-constructor-{name}-O{opt}'
            c, native, module = (prefix.with_suffix(ext) for ext in ('.c', '.native', '.wasm'))
            run([exe, f'-O{opt}', '--standalone', '-o', c, path])
            run([cc, c, '-pthread', '-lm', '-ldl', '-o', native])
            reference = run([native], ok=False)
            assert reference.returncode != 0 and reference.stdout == b'before\n' and reason in reference.stderr
            run([exe, f'-O{opt}', '--target', 'wasm', '-o', module, path])
            text = run([validator, 'print', module]).stdout.decode()
            text = text[:text.rfind(')')] + '  (export "test_stack_top_0" (global 0))\n)\n'
            wat = prefix.with_suffix('.wat'); wat.write_text(text)
            observed = out / f'array-constructor-{name}-observed-O{opt}.wasm'
            run([validator, 'parse', wat, '-o', observed]); run([validator, 'validate', observed])
            result = run([node, ROOT / 'test/wasm_constructor_assignment_failure.mjs', observed, mode])
            assert result.stdout == b'before\n' and not result.stderr
            count += 1
    return count
