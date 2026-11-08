"""Ordered array values, complete live images and guarded slice boundaries."""
from pathlib import Path
import re
from wasm_data_iteration_checks import function_span
ROOT = Path(__file__).resolve().parents[1]


def check_images(run, node, validator, out):
    count = 0
    for opt in (0, 2):
        module = out / f'wasm_temporary_equality_owner-O{opt}.wasm'
        text = run([validator, 'print', module]).stdout.decode()
        def emit(name, value):
            wat = out / f'temporary-equality-{name}-O{opt}.wat'; wasm = wat.with_suffix('.wasm')
            wat.write_text(value[:value.rfind(')')] + '  (export "test_stack_top_0" (global 0))\n)\n')
            run([validator, 'parse', wat, '-o', wasm]); run([validator, 'validate', wasm])
            return wasm
        result = run([node, ROOT / 'test/wasm_temporary_equality_owner.mjs', emit('owner', text)])
        assert result.stdout == b'before\nright-live\nafter\n' and not result.stderr
        count += 1
        a, z = function_span(text, 'main'); body = text[a:z]
        copies = list(re.finditer(r'(?m)^\s*memory.copy(?: 0 0)?\s*$', body)); assert len(copies) == 1
        copy = copies[0]
        missing_copy = body[:copy.start()] + '\n      drop\n      drop\n      drop\n' + body[copy.end():]
        result = run([node, ROOT / 'test/wasm_temporary_equality_owner.mjs',
                      emit('missing-capture', text[:a] + missing_copy + text[z:])], ok=False)
        assert result.returncode == 1 and b'temporary equality captured image differs' in result.stderr
        count += 1
        bases = re.findall(r'i32.const 16\s+call \$goose.reserve_frame\s+local.set (\S+)', body)
        assert len(bases) == 2
        calls = list(re.finditer(r'(?m)^\s*call \$change\.\d+\s*$', body)); assert len(calls) == 1
        call = calls[0]
        early = body[:call.start()] + f'\n      local.get {bases[0]}\n      global.set 0\n' + body[call.start():]
        restores = list(re.finditer(r'(?m)^\s*global.set 0\s*$', body)); assert len(restores) == 2
        restore = restores[-1]
        missing_restore = body[:restore.start()] + '\n      drop\n' + body[restore.end():]
        for name, modified in [('early-release', early), ('missing-restore', missing_restore)]:
            result = run([node, ROOT / 'test/wasm_temporary_equality_owner.mjs',
                          emit(name, text[:a] + modified + text[z:])], ok=False)
            assert result.returncode == 1 and b'temporary equality live frame top differs' in result.stderr
            count += 1
    return count


def check_guards(run, exe, cc, out):
    cases = {
        'explicit-slices': ('fn main(){var a:i64[2]=[7,8];var b:i64[2]=[7,8];'
                            'assert(a[..]==b[..]);print("guarded");}\n',
                            b'slice equality needs the pending view lowering'),
        'nonfixed-view': ('recursive fn make()->i64[2]{return[7,8];}\n'
                          'fn main(){var a:i64[]=[7,8];assert(a==make());print("guarded");}\n',
                          b'comparison views need the pending nonfixed owner lowering'),
    }
    count = 0
    for name, (source_text, reason) in cases.items():
        source = out / f'temporary-equality-{name}-guard.goose'; source.write_text(source_text)
        for opt in (0, 2):
            prefix = out / f'temporary-equality-{name}-guard-O{opt}'
            c, native, module = (prefix.with_suffix(ext) for ext in ('.c', '.native', '.wasm'))
            run([exe, f'-O{opt}', '--standalone', '-o', c, source])
            run([cc, c, '-pthread', '-lm', '-ldl', '-o', native])
            reference = run([native]); assert reference.stdout == b'guarded\n' and not reference.stderr
            module.unlink(missing_ok=True)
            result = run([exe, f'-O{opt}', '--target', 'wasm', '-o', module, source], ok=False)
            assert result.returncode == 1 and reason in result.stderr, (name, opt, result.stderr)
            assert not module.exists()
            count += 1
    return count
