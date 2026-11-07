"""Live temporary owners and validated missing-restore controls."""
from pathlib import Path
import re
from wasm_data_iteration_checks import function_span
ROOT = Path(__file__).resolve().parents[1]


def check_owners(run, node, validator, out):
    count = 0
    for opt in (0, 2):
        for name, frame, temporary in [('loop', 0, 8), ('early', 0, 8),
                                       ('growth', 8, 8), ('global', 0, 8), ('exits', 0, 16),
                                       ('empty', 2, 1), ('variant_empty', 2, 1), ('nested_assignment', 0, 16),
                                       ('array_scalar_exit', 0, 16), ('array_aggregate_exit', 0, 16),
                                       ('array_scalar_limited_exit', 0, 16),
                                       ('array_aggregate_limited_exit', 0, 16), ('data_exit', 0, 8)]:
            module = out / f'wasm_constructor_assignment_{name}-O{opt}.wasm'
            text = run([validator, 'print', module]).stdout.decode()
            if name in ('empty', 'variant_empty'):
                a, z = function_span(text, 'main')
                assert re.search(r'i32.const 1\s+call \$goose.reserve_frame', text[a:z])
            def emit(suffix, wat):
                wat = wat[:wat.rfind(')')] + '  (export "test_stack_top_0" (global 0))\n)\n'
                path = out / f'constructor-{name}-{suffix}-O{opt}.wat'
                path.write_text(wat)
                wasm = path.with_suffix('.wasm')
                run([validator, 'parse', path, '-o', wasm])
                run([validator, 'validate', wasm])
                return wasm
            healthy = emit('owner', text)
            result = run([node, ROOT / 'test/wasm_constructor_assignment.mjs', healthy,
                          name, str(frame), str(temporary)])
            expected = (ROOT / 'test/expected' / f'wasm_constructor_assignment_{name}.out').read_bytes()
            assert result.stdout == expected and not result.stderr, (name, result.stdout, result.stderr)
            count += 1
            if name != 'loop':
                continue
            a, z = function_span(text, 'main')
            body = text[a:z]
            # This function has no named frame. Its first Memory 0 restore
            # belongs to the constructor temporary inside the loop.
            changed, n = re.subn(r'(?m)^(\s*)global.set (?:0|\$[^\s]+)\s*$',
                                  r'\1drop', body, count=1)
            assert n == 1
            damaged = emit('missing-restore', text[:a] + changed + text[z:])
            result = run([node, ROOT / 'test/wasm_constructor_assignment.mjs', damaged,
                          name, str(frame), str(temporary)], ok=False)
            assert result.returncode == 1 and b'constructor temporary live frame top differs' in result.stderr, result.stderr
            count += 1
    return count


def check_failure(run, exe, cc, node, validator, out):
    source = out / 'constructor-failure.goose'
    source.write_text('struct S { a: i64, b: i64 }\n'
                      'var target: S = S { a: 1, b: 2 };\n'
                      'var divisor: i64 = 0;\n'
                      'fn main() { print("before"); target = S { a: 9, b: 8 / divisor }; print("after"); }\n')
    count = 0
    for opt in (0, 2):
        prefix = out / f'constructor-failure-O{opt}'
        c, native, module = (prefix.with_suffix(ext) for ext in ('.c', '.native', '.wasm'))
        run([exe, f'-O{opt}', '--standalone', '-o', c, source])
        run([cc, c, '-pthread', '-lm', '-ldl', '-o', native])
        result = run([native], ok=False)
        assert result.returncode != 0 and result.stdout == b'before\n' and b'division by zero' in result.stderr
        run([exe, f'-O{opt}', '--target', 'wasm', '-o', module, source])
        text = run([validator, 'print', module]).stdout.decode()
        text = text[:text.rfind(')')] + '  (export "test_stack_top_0" (global 0))\n)\n'
        wat = prefix.with_suffix('.wat'); wat.write_text(text)
        checked = out / f'constructor-failure-observed-O{opt}.wasm'
        run([validator, 'parse', wat, '-o', checked]); run([validator, 'validate', checked])
        result = run([node, ROOT / 'test/wasm_constructor_assignment_failure.mjs', checked])
        assert result.stdout == b'before\n' and not result.stderr, (result.stdout, result.stderr)
        count += 1
    return count


def check_target_failure(run, exe, cc, node, validator, out):
    source = out / 'constructor-target-bounds.goose'
    source.write_text('struct S { n: i64 }\n'
                      'var index: i64 = 1;\n'
                      'recursive fn effect() -> i64 { print("rhs"); return 9; }\n'
                      'fn main() { var rows: S[] = [S { n:1 }]; print("before"); '
                      'rows[index] = S { n:effect() }; print("after"); }\n')
    count = 0
    for opt in (0, 2):
        prefix = out / f'constructor-target-bounds-O{opt}'
        c, native, module = (prefix.with_suffix(ext) for ext in ('.c', '.native', '.wasm'))
        run([exe, f'-O{opt}', '--standalone', '-o', c, source])
        run([cc, c, '-pthread', '-lm', '-ldl', '-o', native])
        result = run([native], ok=False)
        assert result.returncode != 0 and result.stdout == b'before\n'
        assert b'index 1 out of bounds (length 1)' in result.stderr
        run([exe, f'-O{opt}', '--target', 'wasm', '-o', module, source])
        text = run([validator, 'print', module]).stdout.decode()
        text = text[:text.rfind(')')] + '  (export "test_stack_top_0" (global 0))\n)\n'
        wat = prefix.with_suffix('.wat'); wat.write_text(text)
        checked = out / f'constructor-target-bounds-observed-O{opt}.wasm'
        run([validator, 'parse', wat, '-o', checked]); run([validator, 'validate', checked])
        result = run([node, ROOT / 'test/wasm_constructor_assignment_failure.mjs', checked, 'bounds'])
        assert result.stdout == b'before\n' and not result.stderr, (result.stdout, result.stderr)
        count += 1
    return count
