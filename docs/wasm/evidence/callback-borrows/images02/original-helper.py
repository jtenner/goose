"""Borrowed temporary owners, complete frame images and specific fault controls."""
from pathlib import Path
import json
import re
from wasm_data_iteration_checks import function_span
from wasm_fixed_binary_checks import emit
ROOT = Path(__file__).resolve().parents[1]


def check_images(run, node, validator, out):
    count = 0
    expected = b'before\nargument-live\nbody-live\nafter\nargument-live\nbody-live\nafter\n'
    for opt in (0, 2):
        text = run([validator, 'print', out / f'wasm_callback_borrow_owner-O{opt}.wasm']).stdout.decode()
        args = [node, ROOT / 'test/wasm_callback_borrow_owner.mjs']
        name = f'callback-borrow-owner-O{opt}'
        metadata = out / (name + '.json')
        result = run(args + [emit(run, validator, out, name + '-healthy', text), metadata])
        assert result.stdout == expected and not result.stderr
        count += 1
        initial = json.loads(metadata.read_text())['initial']
        a, z = function_span(text, 'apply'); body = text[a:z]
        bases = re.findall(r'i32.const 11\s+call \$goose.reserve_frame\s+local.set (\S+)', body)
        assert len(bases) == 1
        base = bases[0]
        controls = []
        calls = list(re.finditer(r'(?m)^\s*call \$noise\.\d+\s*$', body))
        assert len(calls) == 1
        call = calls[0]
        for label, point in [('before-noise', call.start()), ('before-body', call.end())]:
            early = body[:point] + f'\n local.get {base}\n global.set 0\n' + body[point:]
            controls.append((label, early, b'callback temporary borrow live frame top differs'))
        missing, n = re.subn(r'(?m)^\s*global.set 0\s*$', '\n drop\n', body)
        assert n == 1
        controls.append(('missing-restore', missing, b'callback temporary borrow live frame top differs'))
        calls = list(re.finditer(r'(?m)^\s*call \$noise\.\d+\s*$', body)); assert len(calls) == 1
        call = calls[0]
        dirty = body[:call.start()] + f'\n i32.const {initial + 64}\n i32.const 0\n i32.store8\n' + body[call.start():]
        controls.append(('outside-byte', dirty, b'callback temporary borrow complete image differs'))
        for label, changed, reason in controls:
            module = emit(run, validator, out, name + '-' + label, text[:a] + changed + text[z:])
            result = run(args + [module], ok=False)
            assert result.returncode == 1 and reason in result.stderr, (label, result.stderr)
            count += 1
        a, z = function_span(text, 'make'); body = text[a:z]
        wrong, n = re.subn(r'\bi64.const 700\b', 'i64.const 701', body); assert n == 1
        module = emit(run, validator, out, name + '-wrong-value', text[:a] + wrong + text[z:])
        result = run(args + [module], ok=False)
        assert result.returncode == 1 and b'callback temporary borrow complete image differs' in result.stderr
        count += 1
        text = run([validator, 'print', out / f'wasm_callback_borrow_growth-O{opt}.wasm']).stdout.decode()
        args = [node, ROOT / 'test/wasm_temporary_borrow_growth.mjs']
        name = f'callback-borrow-growth-O{opt}'
        metadata = out / (name + '.json')
        result = run(args + [emit(run, validator, out, name + '-healthy', text), metadata])
        assert result.stdout == b'growth\n' and not result.stderr
        count += 1
        initial = json.loads(metadata.read_text())['initial']
        a, z = function_span(text, 'apply'); body = text[a:z]
        calls = list(re.finditer(r'(?m)^\s*call \$noise\.\d+\s*$', body)); assert len(calls) == 1
        call = calls[0]
        dirty = body[:call.end()] + f'\n i32.const {initial + 8 + 72000 + 16}\n i32.const 90\n i32.store8\n' + body[call.end():]
        module = emit(run, validator, out, name + '-outside-byte', text[:a] + dirty + text[z:])
        result = run(args + [module], ok=False)
        assert result.returncode == 1 and b'temporary borrow growth image differs' in result.stderr
        count += 1
    return count


def check_guards(run, exe, cc, out):
    common = ('recursive fn noise()->i64{var a:i64[2]=[99,100];return a[0];} '
              'recursive fn read(p:i64&?,x:i64)->i64{if p{return p;}return 0;} ')
    cases = {
        'field': 'struct S{n:i64} recursive fn make()->S{return S{7};} ' + common +
                 'fn apply<F>()->i64{read(F(make().n),noise())} '
                 'fn main(){assert(apply(){p:i64&? =>p}==7);print("guard");}',
        'element': 'recursive fn make()->i64[2]{return [7,8];} ' + common +
                   'fn apply<F>()->i64{read(F(make()[0]),noise())} '
                   'fn main(){assert(apply(){p:i64&? =>p}==7);print("guard");}',
    }
    count = 0
    for name, text in cases.items():
        source = out / f'callback-borrow-{name}-guard.goose'; source.write_text(text + '\n')
        for opt in (0, 2):
            prefix = out / f'callback-borrow-{name}-guard-O{opt}'
            c, native, module = (prefix.with_suffix(ext) for ext in ('.c', '.native', '.wasm'))
            run([exe, f'-O{opt}', '--standalone', '-o', c, source])
            run([cc, c, '-pthread', '-lm', '-ldl', '-o', native])
            result = run([native]); assert result.stdout == b'guard\n' and not result.stderr
            result = run([exe, f'-O{opt}', '--target', 'wasm', '-o', module, source], ok=False)
            reason = (b'aggregate results need the pending destination lowering' if name == 'field' else
                      b'array-valued temporary results need the pending destination lowering')
            assert result.returncode == 1 and reason in result.stderr
            assert not module.exists()
            count += 1
    return count
