"""Scoped temporary reads, complete live images, and address-lifetime guards."""
from pathlib import Path
import re
from wasm_data_iteration_checks import function_span
ROOT = Path(__file__).resolve().parents[1]


def check_images(run, node, validator, out):
    count = 0
    for opt in (0, 2):
        module = out / f'wasm_temporary_read_owner-O{opt}.wasm'
        text = run([validator, 'print', module]).stdout.decode()
        def emit(name, value):
            wat = out / f'temporary-read-{name}-O{opt}.wat'; wasm = wat.with_suffix('.wasm')
            wat.write_text(value[:value.rfind(')')] + '  (export "test_stack_top_0" (global 0))\n)\n')
            run([validator, 'parse', wat, '-o', wasm]); run([validator, 'validate', wasm])
            return wasm
        result = run([node, ROOT / 'test/wasm_temporary_read_owner.mjs', emit('owner', text)])
        assert result.stdout == b'before\nindex-live\nafter\n' and not result.stderr
        count += 1
        a, z = function_span(text, 'main'); body = text[a:z]
        base = re.findall(r'i32.const 16\s+call \$goose.reserve_frame\s+local.set (\S+)', body)
        assert len(base) == 1
        calls = list(re.finditer(r'(?m)^\s*call \$index\.\d+\s*$', body)); assert len(calls) == 1
        call = calls[0]
        early = body[:call.start()] + f'\n      local.get {base[0]}\n      global.set 0\n' + body[call.start():]
        restores = list(re.finditer(r'(?m)^\s*global.set 0\s*$', body)); assert len(restores) == 1
        restore = restores[0]
        missing = body[:restore.start()] + '\n      drop\n' + body[restore.end():]
        for name, modified in [('early-release', early), ('missing-restore', missing)]:
            result = run([node, ROOT / 'test/wasm_temporary_read_owner.mjs',
                          emit(name, text[:a] + modified + text[z:])], ok=False)
            assert result.returncode == 1 and b'temporary read live frame top differs' in result.stderr
            count += 1
        a, z = function_span(text, 'make'); body = text[a:z]
        modified, n = re.subn(r'i64.const 8(?=\s+i64.store)', 'i64.const 9', body); assert n == 1
        result = run([node, ROOT / 'test/wasm_temporary_read_owner.mjs',
                      emit('wrong-image', text[:a] + modified + text[z:])], ok=False)
        assert result.returncode == 1 and b'temporary read live image differs' in result.stderr
        count += 1
    return count


def check_guards(run, exe, cc, out):
    cases = {
        'field': 'struct S{n:i64}\nrecursive fn make()->S{return S{n:7};}\n'
                 'recursive fn read(p:i64&)->i64{return p;}\n'
                 'fn main(){assert(read(make().n)==7);print("borrow_guard");}\n',
        'element': 'recursive fn make()->i64[2]{return[7,8];}\n'
                   'recursive fn read(p:i64&)->i64{return p;}\n'
                   'fn main(){assert(read(make()[1])==8);print("borrow_guard");}\n',
    }
    count = 0
    for name, source_text in cases.items():
        source = out / f'temporary-read-{name}-guard.goose'; source.write_text(source_text)
        for opt in (0, 2):
            prefix = out / f'temporary-read-{name}-guard-O{opt}'
            c, native, module = (prefix.with_suffix(ext) for ext in ('.c', '.native', '.wasm'))
            run([exe, f'-O{opt}', '--standalone', '-o', c, source])
            run([cc, c, '-pthread', '-lm', '-ldl', '-o', native])
            reference = run([native]); assert reference.stdout == b'borrow_guard\n' and not reference.stderr
            module.unlink(missing_ok=True)
            result = run([exe, f'-O{opt}', '--target', 'wasm', '-o', module, source], ok=False)
            reason = (b'aggregate results need the pending destination lowering' if name == 'field' else
                      b'array-valued temporary results need the pending destination lowering')
            assert result.returncode == 1 and reason in result.stderr
            assert not module.exists()
            count += 1
    return count
