"""Stored-layout recovery, value snapshots and exits for array expressions."""
from pathlib import Path
import json,re
from wasm_data_iteration_checks import function_span
from wasm_fixed_binary_checks import emit
ROOT = Path(__file__).resolve().parents[1]


def one(text, pattern, value):
    text, n = re.subn(pattern, value, text, count=1); assert n == 1, pattern
    return text


def check_defer(run, node, validator, out):
    count = 0
    for opt in (0, 2):
        for mode, size in [('fixed', 2), ('limited', 4)]:
            text = run([validator, 'print', out / f'wasm_array_expression_source_{mode}_defer-O{opt}.wasm']).stdout.decode()
            args = [node, ROOT / 'test/wasm_array_expression_defer.mjs']; record = out / f'expression-defer-{mode}-O{opt}.json'
            module = emit(run, validator, out, f'expression-defer-{mode}-healthy-O{opt}', text, 2)
            result = run(args + [module, mode, record]); assert result.stdout == b'inside\nafter\n' and not result.stderr
            count += 1
            state = json.loads(record.read_text()); a,z = function_span(text, 'main'); body = text[a:z]
            copy_arg = r'i32.const 2(?=\n\s*memory.copy 1 0\b)' if mode == 'fixed' else r'local.get \d+(?=\n\s*memory.copy 1 0\b)'
            if mode == 'fixed':
                late = one(body, r'local.get \d+(?=\n\s*i32.const 2\n\s*memory.copy 1 0\b)', f'i32.const {state["payload"]}')
            else:
                late = one(body, r'local.get \d+\n\s*i32.const 1\n\s*i32.add(?=\n\s*local.get \d+\n\s*memory.copy 1 0\b)', f'i32.const {state["payload"]}')
            controls = [
                ('late-read', late, b'expression data image differs'),
                ('short', one(body, copy_arg, 'i32.const 1'), b'expression data image differs'),
                ('long', one(body, copy_arg, 'i32.const 3'), b'expression data image differs'),
                ('reserve', one(body, rf'i32.const {size}(?=\n\s*call \$goose.reserve_frame)', f'i32.const {size - 1}'), b'expression source reservation differs'),
                ('temporary', one(body, r'global.set 0\b', 'drop'), b'expression source temporary was not released'),
                ('data', one(body, r'global.set 1\b', 'drop'), b'expression completed data top differs'),
            ]
            for label, changed, reason in controls:
                module = emit(run, validator, out, f'expression-defer-{mode}-{label}-O{opt}', text[:a]+changed+text[z:], 2)
                result = run(args + [module, mode], ok=False)
                assert result.returncode == 1 and reason in result.stderr, (mode, label, result.stderr)
                count += 1
    return count


def check_inline(run, node, validator, out):
    count = 0
    for opt in (0, 2):
        for mode in ('fixed', 'limited'):
            text = run([validator, 'print', out / f'wasm_array_expression_source_{mode}_inline_opaque-O{opt}.wasm']).stdout.decode()
            args = [node, ROOT / 'test/wasm_array_expression_inline.mjs']
            result = run(args + [emit(run, validator, out, f'expression-inline-{mode}-healthy-O{opt}', text, 2), mode])
            assert result.stdout == b'true\nfalse\nopaque\n' and not result.stderr; count += 1
            a,z = function_span(text, 'main'); body = text[a:z]; changed = one(body, r'global.set 0\b', 'drop')
            result = run(args + [emit(run, validator, out, f'expression-inline-{mode}-leak-O{opt}', text[:a]+changed+text[z:], 2), mode], ok=False)
            assert result.returncode == 1 and any(reason in result.stderr for reason in (b'expression inline live frame top differs', b'expression inline completed frame top differs')), result.stderr
            count += 1
    return count


def check_guards(run, exe, cc, out):
    count = 0
    for kind, left, right, values, n in [('fixed','[2]','[3]','[9,10,11]',3), ('limited','[..3]','[..4]','[9,10,11,12]',4)]:
        source = (f'recursive fn probe(yes:bool){{var a:u8{left}=[7,8];var c:u8{right}={values};'
                  f'var b:u8[]=if yes{{a}}else{{c}};assert(b.len==(if yes{{2}}else{{{n}}}));}}'
                  'fn main(){probe(true);probe(false);print("mixed");}\n')
        path = out / f'array-expression-mixed-{kind}.goose'; path.write_text(source)
        for opt in (0,2):
            prefix = out / f'array-expression-mixed-{kind}-O{opt}'; c,native,module = (prefix.with_suffix(ext) for ext in ('.c','.native','.wasm'))
            run([exe,f'-O{opt}','--standalone','-o',c,path]);run([cc,c,'-pthread','-lm','-ldl','-o',native]); result=run([native]);assert result.stdout==b'mixed\n' and not result.stderr
            result=run([exe,f'-O{opt}','--target','wasm','-o',module,path],ok=False)
            assert result.returncode==1 and b'array-valued temporary results need the pending destination lowering' in result.stderr and not module.exists(),result.stderr
            count+=1
    return count
