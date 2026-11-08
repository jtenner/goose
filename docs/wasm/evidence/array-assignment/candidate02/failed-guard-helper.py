"""Exact array images, opaque reference guards and retained policy gates."""
from pathlib import Path
import re
from wasm_data_iteration_checks import function_span
ROOT = Path(__file__).resolve().parents[1]


def check_images(run, node, validator, out):
    count = 0
    for opt in (0, 2):
        module = out / f'wasm_array_assignment_image-O{opt}.wasm'
        text = run([validator, 'print', module]).stdout.decode()
        def emit(name, value):
            value = value[:value.rfind(')')] + '  (export "test_stack_top_0" (global 0))\n)\n'
            wat = out / f'array-assignment-image-{name}-O{opt}.wat'; wasm = wat.with_suffix('.wasm')
            wat.write_text(value); run([validator, 'parse', wat, '-o', wasm]); run([validator, 'validate', wasm])
            return wasm
        healthy = emit('owner', text)
        result = run([node, ROOT / 'test/wasm_array_assignment_image.mjs', healthy])
        assert result.stdout == b'seed\ncopied\n' and not result.stderr
        count += 1
        a, z = function_span(text, 'main'); body = text[a:z]
        length = r'i32.const 9(?=\s+memory.copy(?: 0 0)?\s)'
        copies = list(re.finditer(length, body)); assert len(copies) == 1
        changed = [('short', re.sub(length, 'i32.const 8', body)),
                   ('long', re.sub(length, 'i32.const 10', body))]
        omitted, n = re.subn(r'(?m)^(\s*)memory.copy(?: 0 0)?\s*$',
                              r'\1drop\n\1drop\n\1drop', body, count=1)
        assert n == 1; changed.append(('omitted', omitted))
        offsets = list(re.finditer(r'i32.const 9(?=\s+i32.add)', body[:copies[0].start()]))
        assert offsets
        source = offsets[-1]
        changed.append(('source', body[:source.start()] + 'i32.const 8' + body[source.end():]))
        for name, wrong in changed:
            damaged = emit(name, text[:a] + wrong + text[z:])
            result = run([node, ROOT / 'test/wasm_array_assignment_image.mjs', damaged], ok=False)
            assert result.returncode == 1 and b'exact array assignment Memory 0 image differs' in result.stderr, (name, result.stderr)
            assert result.stdout == b'seed\n', (name, result.stdout)
            count += 1
    return count


def check_references(run, node, validator, wasmtime_python, out):
    count = 0
    for opt in (0, 2):
        module = out / f'wasm_array_assignment_field_carry-O{opt}.wasm'
        text = run([validator, 'print', module]).stdout.decode()
        a, z = function_span(text, 'main'); body = text[a:z]
        calls = list(re.finditer(r'(?m)^(\s*)call (\$set_h\.\d+)\s*$', body))
        assert len(calls) == 2
        call = calls[0]
        locals_ = list(re.finditer(r'(?m)^    \(local[^\n]*\)\n', body))
        assert locals_
        # Append one named local so all original numeric local indexes stay valid.
        at = locals_[-1].end()
        def mutant(name, prefix):
            modified = body[:call.start()] + prefix + '\n    call ' + call[2] + body[call.end():]
            modified = modified[:at] + '    (local $array_fault_source i64)\n' + modified[at:]
            wat = out / f'array-assignment-reference-{name}-O{opt}.wat'; wasm = wat.with_suffix('.wasm')
            wat.write_text(text[:a] + modified + text[z:])
            run([validator, 'parse', wat, '-o', wasm]); run([validator, 'validate', wasm])
            return wasm
        bad = [
            ('null', 'i64.const 0', b'null reference'),
            ('identity', f'i64.const {(127 << 32) | 1}', b'invalid memory identity or watermark'),
            ('bounds', 'i64.const 4294967296\n    memory.size 1\n    i64.extend_i32_u\n    i64.const 16\n    i64.shl\n    i64.const 4\n    i64.sub\n    i64.or', b'out of bounds'),
            ('carry', f'i64.const {(1 << 32) | 0xffffffff}', b'memory32 address overflow'),
        ]
        variants = []
        for name, pointer, reason in bad:
            variants.append(('target-' + name, '    local.set $array_fault_source\n    drop\n    ' + pointer + '\n    local.get $array_fault_source', reason))
            variants.append(('source-' + name, '    drop\n    ' + pointer, reason))
        variants.append(('namespace', '    local.set $array_fault_source\n    i64.const 4294967295\n    i64.and\n    local.get $array_fault_source', b'assert failed'))
        for name, prefix, reason in variants:
            damaged = mutant(name, prefix)
            engines = [[node, ROOT / 'scripts/run_wasm.mjs', damaged]]
            if wasmtime_python:
                engines.append([wasmtime_python, ROOT / 'test/wasmtime_host.py', damaged])
            for command in engines:
                result = run(command, ok=False)
                assert result.returncode == 1 and reason in result.stderr, (name, result.stderr)
                assert not result.stdout, (name, result.stdout)
                count += 1
    return count


def check_guards(run, exe, cc, node, out):
    cases = [
        ('literal', 'fn main(){var a:u8[2]=[1,2];a=[3,4];print(a[0]);}\n',
         b'3\n', b'whole-array assignment from a temporary needs the pending destination lowering'),
        ('default', 'struct S{n:i64=7}\nfn main(){var a:S[1]=[S{n:1}];a=default<S[1]>();print(a[0].n);}\n',
         b'7\n', b'whole-array assignment from a temporary needs the pending destination lowering'),
        ('data', 'fn main(){var a:u8[]=[1];var b:u8[]=[2];a=b;print(a[0]);}\n',
         b'2\n', b'whole-array assignment needs the pending destination lowering'),
        ('adaptation', 'fn main(){var a:u8[..3]=[1];var b:u8[2]=[2,3];a=b;print(a.len);}\n',
         b'2\n', b'whole-array assignment adaptation needs the pending destination lowering'),
    ]
    count = 0
    for name, text, expected, reason in cases:
        source = out / f'array-assignment-{name}-guard.goose'; source.write_text(text)
        for opt in (0, 2):
            prefix = out / f'array-assignment-{name}-guard-O{opt}'
            c, native, module = (prefix.with_suffix(ext) for ext in ('.c', '.native', '.wasm'))
            run([exe, f'-O{opt}', '--standalone', '-o', c, source])
            run([cc, c, '-pthread', '-lm', '-ldl', '-o', native])
            reference = run([native]); assert reference.stdout == expected and not reference.stderr
            module.unlink(missing_ok=True)
            result = run([exe, f'-O{opt}', '--target', 'wasm', '-o', module, source], ok=False)
            assert result.returncode == 1 and re.findall(rb'wasm target: ([^\n]+)', result.stderr) == [reason], (name, result.stderr)
            assert not module.exists()
            count += 1
    return count
