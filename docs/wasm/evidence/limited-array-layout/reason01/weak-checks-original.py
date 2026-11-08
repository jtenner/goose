"""Limited-array payload bounds, length widths, memory identity and failure atomicity."""
from pathlib import Path
import re
from wasm_data_iteration_checks import function_span
from wasm_fixed_binary_checks import emit
ROOT = Path(__file__).resolve().parents[1]


def check_images(run, node, validator, out):
    count = 0
    for opt in (0, 2):
        for data in (False, True):
            suffix = 'owner_data' if data else 'owner'
            text = run([validator, 'print', out / f'wasm_limited_array_layout_{suffix}-O{opt}.wasm']).stdout.decode()
            args = [node, ROOT / ('test/wasm_limited_array_data.mjs' if data else 'test/wasm_limited_array_owner.mjs')]
            def observed(label, value, ok=True):
                return run(args + [emit(run, validator, out, f'limited-layout-{suffix}-{label}-O{opt}', value, 3 if data else 1)], ok=ok)
            result = observed('healthy', text); assert result.stdout == b'before\nafter\n' and not result.stderr
            count += 1
            a, z = function_span(text, 'main'); body = text[a:z]
            stride = 1 if data else 14
            def size(new):
                changed, n = re.subn(rf'i64.const {stride}(?=\n\s*i64.mul\n\s*i32.wrap_i64)', f'i64.const {new}', body)
                assert n == 1
                return changed
            controls = [('short', size(0 if data else 7)), ('long', size(2 if data else 21))]
            if data:
                width, n = re.subn(r'i64.store16 2 offset=5\b', 'i64.store8 2 offset=5', body); assert n == 1
                memory, n = re.subn(r'i64.store16 2 offset=5\b', 'i64.store16 1 offset=5', body); assert n == 1
                controls += [('width', width), ('memory', memory)]
                reason = b'limited data '
            else:
                index = body.index('memory.copy')
                tail, n = re.subn(r'local.get \d+(?=\n\s*i64.store8\b)', 'i64.const 3', body[index:], count=1); assert n == 1
                restore, n = re.subn(r'global.set 0\b', 'drop', body, count=1); assert n == 1
                controls += [('count', body[:index] + tail), ('restore', restore)]
                reason = b'limited layout '
            for label, modified in controls:
                result = observed(label, text[:a] + modified + text[z:], False)
                assert result.returncode == 1 and reason in result.stderr, (suffix, label, result.stderr)
                count += 1
    return count


def check_failures(run, exe, cc, node, validator, wasmtime_python, out):
    count = 0
    source = ('var calls:i64=0;var target:u8[..3]=[1,2,3];\n'
              'recursive fn make()->u8[..256]{calls++;target[2]=99;print("rhs");return[7,8,9,10];}\n'
              'fn main(){print("before");target=make();print("after");}\n')
    path = out / 'limited-layout-capacity.goose'; path.write_text(source)
    for opt in (0, 2):
        prefix = out / f'limited-layout-capacity-O{opt}'
        c, native, module = (prefix.with_suffix(ext) for ext in ('.c', '.native', '.wasm'))
        run([exe, f'-O{opt}', '--standalone', '-o', c, path])
        original = c.read_text()
        hooked, n = re.subn(r'(static GS_NORETURN void gs_fail\([^\n]+\) \{)',
                           'static void test_limited_state(void);\n\\1\n    test_limited_state();', original)
        assert n == 1
        hooked += ('\nstatic void test_limited_state(void) {\n'
                   '    fprintf(stderr,"limited-state=%lld,%lld,%lld,%lld,%lld\\n",'
                   '(long long)GS_GL->calls_g,(long long)GS_GL->target_g.len,'
                   '(long long)GS_GL->target_g.e[0],(long long)GS_GL->target_g.e[1],'
                   '(long long)GS_GL->target_g.e[2]);\n}\n')
        compiled = out / (prefix.name + '-observed.c'); compiled.write_text(hooked)
        run([cc, f'-O{opt}', compiled, '-pthread', '-lm', '-ldl', '-o', native])
        result = run([native], ok=False)
        assert result.returncode != 0 and result.stdout == b'before\nrhs\n' and b'capacity' in result.stderr, result.stderr
        assert result.stderr.startswith(b'limited-state=1,3,1,2,99\n'), result.stderr
        run([exe, f'-O{opt}', '--target', 'wasm', '-o', module, path])
        text = run([validator, 'print', module]).stdout.decode()
        args = [node, ROOT / 'test/wasm_limited_array_failure.mjs']
        result = run(args + [emit(run, validator, out, prefix.name + '-healthy', text)])
        assert result.stdout == b'before\nrhs\n' and not result.stderr
        if wasmtime_python:
            result = run([wasmtime_python, ROOT / 'test/wasmtime_host.py', module], ok=False)
            assert result.returncode == 1 and result.stdout == b'before\nrhs\n' and b'capacity' in result.stderr
        count += 1
        a, z = function_span(text, 'main'); body = text[a:z]
        modified, n = re.subn(r'i64.gt_u\b', 'i64.lt_u', body); assert n == 1
        result = run(args + [emit(run, validator, out, prefix.name + '-guard', text[:a] + modified + text[z:])], ok=False)
        assert result.returncode == 1 and b'limited capacity' in result.stderr, result.stderr
        count += 1
    return count


def check_wide(run, node, validator, out):
    count = 0
    for opt in (0, 2):
        text = run([validator, 'print', out / f'wasm_limited_array_layout_owner_wide-O{opt}.wasm']).stdout.decode()
        args = [node, ROOT / 'test/wasm_limited_array_wide.mjs']
        def observed(label, value, ok=True):
            return run(args + [emit(run, validator, out, f'limited-wide-{label}-O{opt}', value)], ok=ok)
        result = observed('healthy', text); assert result.stdout == b'before\nwide\nafter\n' and not result.stderr
        count += 1
        a, z = function_span(text, 'main'); body = text[a:z]
        wide, n = re.subn(r'i64.store32\b', 'i64.store16', body); assert n == 1
        narrow, n = re.subn(r'i64.store16\b', 'i64.store8', body[body.index('memory.copy') + 1:]); assert n == 1
        narrow = body[:body.index('memory.copy') + 1] + narrow
        first, n = re.subn(r'i64.const 1(?=\n\s*i64.mul\n\s*i32.wrap_i64)', 'i64.const 0', body, count=1); assert n == 1
        for label, modified in [('wide-width', wide), ('narrow-width', narrow), ('bytes', first)]:
            result = observed(label, text[:a] + modified + text[z:], False)
            assert result.returncode == 1 and b'limited wide memory 0 image differs' in result.stderr, (label, result.stderr)
            count += 1
    return count
