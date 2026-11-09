"""Complete packed images and active temporary ownership for fills/defaults."""
from pathlib import Path
import re
from wasm_data_iteration_checks import function_span
ROOT = Path(__file__).resolve().parents[1]


def check_modules(run, node, validator, out):
    count = 0
    def emit(name, text):
        text = text[:text.rfind(')')] + '  (export "test_stack_top_0" (global 0))\n)\n'
        wat = out / (name + '.wat'); wasm = wat.with_suffix('.wasm')
        wat.write_text(text)
        run([validator, 'parse', wat, '-o', wasm]); run([validator, 'validate', wasm])
        return wasm
    for opt in (0, 2):
        for name, frame, lines, temporary in [('live_fill', 24, 2, 8), ('live_default', 24, 4, 8),
                                    ('live_zero', 1, 2, 8), ('fill_exit', 16, 3, 8),
                                    ('nested_fill', 32, 1, 8), ('default_growth', 16, 1, 8),
                                    ('nested_defaults', 32, 5, 24), ('prefix16', 2402, 1, 8),
                                    ('prefix32', 560004, 1, 8), ('defer_exit', 0, 1, 8)]:
            module = out / f'wasm_aggregate_construction_{name}-O{opt}.wasm'
            text = run([validator, 'print', module]).stdout.decode()
            observed = emit(f'aggregate-construction-{name}-owner-O{opt}', text)
            result = run([node, ROOT / 'test/wasm_aggregate_construction_owner.mjs', observed,
                          str(frame), str(lines), str(temporary)])
            expected = (ROOT / 'test/expected' / f'wasm_aggregate_construction_{name}.out').read_bytes()
            assert result.stdout == expected and not result.stderr, (name, result.stdout, result.stderr)
            count += 1
        module = out / f'wasm_aggregate_construction_image-O{opt}.wasm'
        text = run([validator, 'print', module]).stdout.decode()
        healthy = emit(f'aggregate-construction-image-owner-O{opt}', text)
        result = run([node, ROOT / 'test/wasm_aggregate_construction_image.mjs', healthy])
        assert result.stdout == b'seed\neval\nfilled\n' and not result.stderr
        count += 1
        a, z = function_span(text, 'main'); body = text[a:z]
        length = r'i32.const 3(?=\s+memory.copy(?: 0 0)?\s)'
        assert len(re.findall(length, body)) == 1
        changed = [('short', re.sub(length, 'i32.const 2', body)),
                   ('long', re.sub(length, 'i32.const 4', body))]
        stride = r'i64.const 3(?=\s+i64.mul)'
        copy_start = re.search(length, body).start()
        assert len(re.findall(stride, body[:copy_start])) == 1
        changed.append(('stride', re.sub(stride, 'i64.const 4', body, count=1)))
        omitted, n = re.subn(r'(?m)^(\s*)memory.copy(?: 0 0)?\s*$',
                              r'\1drop\n\1drop\n\1drop', body, count=1)
        assert n == 1
        changed.append(('omitted', omitted))
        for name, wrong in changed:
            damaged = emit(f'aggregate-construction-image-{name}-O{opt}', text[:a] + wrong + text[z:])
            result = run([node, ROOT / 'test/wasm_aggregate_construction_image.mjs', damaged], ok=False)
            assert result.returncode == 1 and b'aggregate fill complete Memory 0 image differs' in result.stderr, (name, result.stderr)
            assert result.stdout == b'seed\neval\n', (name, result.stdout)
            count += 1
    return count
