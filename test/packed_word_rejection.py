#!/usr/bin/env python3
"""The deferred u128 backing fails once, before any aggregate/C lowering."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

MESSAGE = '128-bit packed word backings are not yet supported'

def check(exe=None):
    exe = exe or os.environ.get('GOOSE_TEST_EXE') or shutil.which('goose++')
    checks = 0
    with tempfile.TemporaryDirectory(prefix='packed-rejection-') as td:
        root = Path(td)
        env = dict(os.environ, GOOSE_HOME=str(root/'home'))
        source, output = root/'reject.goose', root/'reject.c'
        sources = [
            'packed word W:u128 {} fn main(){}',
            'packed word W:u128 { low:u64, high:u64 } fn main(){}',
            'packed word W:u128 { low:u64 } fn main(){ let w=W{1}; }',
            'packed word W:u128 {} packed word Good:u8 { x:u8 } fn main(){let g=Good{1};}',
        ]
        for text in sources:
            source.write_text(text)
            for options in (['--check'], ['--parse'], ['-O0','-o',output], ['-O2','-o',output]):
                p = subprocess.run([exe,*map(str,options),str(source)],env=env,
                                   capture_output=True,text=True,timeout=60)
                diagnostic = p.stdout+p.stderr
                assert p.returncode != 0, (options,text)
                assert diagnostic.count('error:') == 1 and diagnostic.count(MESSAGE) == 1, diagnostic
                assert not output.exists(), 'rejected backing emitted C'
                checks += 1
        for width in (65,127,128,129,9999999999999999999999999):
            source.write_text(f'packed word W:u64 {{ x:u{width} }} fn main(){{}}')
            p = subprocess.run([exe,'--check',str(source)],env=env,capture_output=True,text=True)
            assert p.returncode and 'between 1 and 64' in p.stderr, p.stderr
            checks += 1
        # The scope change must not leave a general u128 type or widened literals.
        for body in ('var x:u128=0;', 'let x=18446744073709551616;',
                     'let x=0x10000000000000000;'):
            source.write_text('fn main(){'+body+'}')
            p = subprocess.run([exe,'--check',str(source)],env=env,capture_output=True,text=True)
            assert p.returncode, body
            checks += 1
    print(f'packed word deferred-backing rejection: {checks} checks passed')
    return checks

if __name__ == '__main__':
    check()
