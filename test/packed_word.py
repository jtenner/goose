#!/usr/bin/env python3
"""Packed-word native acceptance against an independent integer oracle.
All C, executables and runtime caches are scoped to temporary directories.
"""
import os
from pathlib import Path
import random
import shutil
import subprocess
import tempfile


def check(exe=None):
    exe = exe or os.environ.get('GOOSE_TEST_EXE') or shutil.which('goose++')
    rng = random.Random(0x5041434b)
    decls, body, expected = [], [], []
    def output(expression, value):
        body.append(f'print({expression});')
        expected.append(str(value).lower())
    # Every descriptor width, all four backings, and edge/interior offsets.
    for bits in (8, 16, 32, 64):
        for width in range(1, bits + 1):
            offset = (bits - width) // 2
            name = f'W{bits}_{width}'
            prefix = f'_: u{offset},' if offset else ''
            decls.append(f'packed word {name}:u{bits} {{{prefix} value:u{width}}}')
            mask = ((1 << width) - 1) << offset
            for seed in (0, (1 << bits) - 1, int('aa' * (bits//8), 16)):
                value = rng.getrandbits(width)
                body.append(f'var w{len(expected)} = ({seed} as u{bits}) as {name};')
                var = f'w{len(expected)}'
                body.append(f'{var}.value = {value};')
                output(f'{var} as u{bits}', (seed & ~mask) | (value << offset))
                output(f'{var}.value', value)
    decls += ['enum E { A, B, C }',
              'packed word W:u64 { a:u3 = 2, flag:bool = true, e:E = E.B, _:u2, b:u56 = 9 }',
              'struct Box { prefix:u8, w:W }',
              'var global_word = W { .. };',
              'fn identity<T>(w:T) -> T { w }',
              'fn change(w:W&) { w.a = 5; }',
              'fn neighbor(w:W&) -> u8 { w.b = 27; 3 }',
              'fn index(count:i64&) -> i64 { count++; 1 }',
              'fn stamp(count:i64&, value:u8) -> u8 { count++; value }']
    body += ['var w=W { b:7, e:E.C, flag:false, a:3 };']
    output('w as u64', (7<<8) | (2<<4) | 3)
    output('w.e == E.C', True)
    body += ['w.a += 2;', 'w.a++;', 'w.a--;', 'w.a *= 1;', 'w.a /= 2;',
             'w.a %= 2;', 'w.a |= 3;', 'w.a ^= 1;', 'w.a &= 6;', 'w.a >>= -1;', 'w.a <<= 1;']
    output('w.a', 0)
    body += ['w.a *= 65535;', 'w.a = neighbor(w);']
    output('w.b', 27)
    body += ['w.a += neighbor(w);']
    output('w.a', 6)
    output('w.b', 27)
    body += ['var box=Box { 1,w }; box.w.a=2;', 'var arr:W[2]=[w,w]; var count:i64=0;',
             'arr[index(count)].a = stamp(count,1);']
    output('count', 2)
    output('arr[1].a', 1)
    output('arr[0] == w', True)
    output('box.w.a', 2)
    output('identity(w) == w', True)
    body += ['change(w);']
    output('w.a', 5)
    output('global_word as u64', (9<<8) | (1<<4) | 8 | 2)
    body += ['var grow:W[>..]=[w,arr[1]];', 'grow[1].a=4;']
    output('grow[1].a', 4)
    body += ['let image=to_bytes(grow); var restored=from_bytes<W[>..]>(image);']
    output('restored[0] == w', True)
    output('restored[1] == grow[1]', True)
    output('((0 as u64) as W) == ((128 as u64) as W)', False)
    body += ['var invalid=(63 as u64) as W; let rawcopy=invalid; invalid.b=8;']
    output('rawcopy as u64',63)
    output('invalid.a',7)
    output('invalid as u64',(8<<8)|63)
    for count in (1, 2, 3, 4, 5, 256, 257):
        decls += [f'enum E{count} {{' + ','.join(f'V{i}' for i in range(count)) + '}',
                  f'packed word EW{count}:u16 {{ e:E{count}, flag:bool }}']
        body += [f'let e{count}=EW{count} {{ E{count}.V{count-1},true }};']
        output(f'e{count} as u16', (1 << max(1,(count-1).bit_length())) | (count-1))
        output(f'e{count}.e == E{count}.V{count-1}', True)
    with tempfile.TemporaryDirectory(prefix='goose-packed-word-') as td:
        root = Path(td)
        env = dict(os.environ, GOOSE_HOME=str(root/'home'))
        def run(args, fail=False):
            p = subprocess.run(list(map(str,args)),env=env,capture_output=True,text=True,timeout=120)
            assert (p.returncode != 0) == fail, (args,p.returncode,p.stdout[-2000:],p.stderr[:6000])
            return p.stdout+p.stderr
        source=root/'values.goose'
        source.write_text('\n'.join(decls)+'\nfn main(){\n'+'\n'.join(body)+'\n}\n')
        run([exe,'--check','--roundtrip',source])
        checks=1
        for level in (0,2):
            c=root/f'values{level}.c'
            run([exe,f'-O{level}','--standalone','-o',c,source])
            for cc in (os.environ.get('CC','gcc'),os.environ.get('CLANG','clang')):
                binary=root/'values'
                run([cc,'-std=c11',f'-O{level}','-fsanitize=undefined','-fno-sanitize-recover=all',c,'-lm','-pthread','-ldl','-o',binary])
                actual=run([binary]).splitlines()
                assert actual == expected, (cc,level,len(actual),len(expected),[(i,a,b) for i,(a,b) in enumerate(zip(actual,expected)) if a!=b][:10])
                checks += len(expected)
        # All-build traps, including arithmetic before carrier wrap and invalid enums.
        traps = [
            ('packed word T:u8 {a:u3}', 'var w=T{0}; w.a=x;', 'fn value()->u64 {8}'),
            ('packed word T:u8 {a:u8}', 'var w=T{255}; w.a++;', ''),
            ('packed word T:u64 {a:u64}', 'var w=T{18446744073709551615}; w.a+=1;', ''),
            ('packed word T:u8 {a:u3}', 'var w=T{1}; w.a-=2;', ''),
            ('packed word T:u8 {a:u3}', 'var w=T{4}; w.a*=2;', ''),
            ('packed word T:u8 {a:u3}', 'var w=T{4}; w.a<<=1;', ''),
            ('packed word T:u8 {a:u3}', 'var w=T{1}; w.a|=8;', ''),
            ('enum E{A,B,C} packed word T:u8 {e:E}', 'var w=(3 as u8) as T; print(w.e);',''),
            ('enum E{A} packed word T:u8 {e:E}', 'var w=(1 as u8) as T; print(w.e);',''),
        ]
        for i,(decl,statements,helper) in enumerate(traps):
            source.write_text(decl+'\n'+helper+'\nfn main(){'+('let x=value();' if helper else '')+statements+'}')
            c=root/'trap.c'; binary=root/'trap'
            run([exe,'--standalone','-o',c,source])
            run(['gcc','-O2',c,'-lm','-pthread','-ldl','-o',binary])
            text=run([binary],fail=True)
            assert 'packed word field' in text,(i,text)
            checks+=1
        for bits in (8,16,32,64):
            source.write_text(f'packed word J:u{bits} {{ a:u3, b:bool, _:u4 }} '
                              f'fn main(){{ var w=((1 as u{bits}) as J); w.a=7; w.b=true; '
                              f'print(w as u{bits}); print(w.a); print(w.b); }}')
            assert run([exe,'--jit',source]).splitlines()==['15','7','true']
            checks+=3
        print(f'packed word native/JIT: {checks} checks passed')
        return checks

if __name__ == '__main__':
    check()
