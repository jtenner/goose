"""Deferred specialization transactions: cycles, exports and root recovery."""
import json
import pathlib
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'scripts'))
from lsp_protocol import Client


def check_transactions(exe, root, core_only=False, fields_only=False, diagnostics_only=False):
    checks = 0

    def invoke(args, ok=True):
        nonlocal checks
        p = subprocess.run([str(exe), *map(str, args)], capture_output=True, text=True, timeout=90)
        assert p.returncode >= 0, (args, p.returncode, p.stderr[-4000:])
        assert (p.returncode == 0) == ok, (args, p.returncode, p.stderr[-4000:])
        checks += 1
        return p

    source = root / 'transaction.goose'
    cfile, header = root / 'transaction.c', root / 'transaction.h'

    def host(expected):
        nonlocal checks
        c = root / 'transaction-host.c'
        c.write_text('#include "transaction.h"\n'
                     'int main(int argc,char **argv){goose_init(argc,argv);'
                     f'return outer()=={expected} ? 0 : 1;}}\n')
        native = root / 'transaction-host'
        p = subprocess.run(['cc', level, str(cfile), str(c), '-o', str(native), '-lm', '-pthread'],
                           capture_output=True, text=True, timeout=90)
        assert p.returncode == 0, p.stderr
        p = subprocess.run([str(native)], capture_output=True, text=True, timeout=10)
        assert p.returncode == 0, (p.returncode, p.stderr)
        checks += 1

    if not diagnostics_only:
        # Exact reviewer library, without main; check its main-bearing form too.
        exact = ('recursive fn stop(n:i64){if n>0 {mid(n-1);} else '
                 '{const if true {return 7 from outer;}}}\n'
                 'recursive fn mid(n:i64){stop(n);}\n'
                 'export fn outer()->i64{stop(3);0}\n')
        for level in ('-O0', '-O2'):
            source.write_text(exact + 'fn main(){}')
            invoke(['check', level, source])
            source.write_text(exact)
            invoke([level, '--standalone', '--header', header, source, '-o', cfile])
            host(7)

        returns = [('selected', 'const if build::CALL {return 7 from outer;}'),
                   ('statement', 'const if build::CALL {return 7 from outer;};'),
                   ('constfor', 'const for <C> in [false,true] {'
                    'const if C && build::CALL {return 7 from outer;}}')]
        if not core_only and not fields_only:
            returns += [('constructor', 'let s=S{const if build::CALL '
                         '{a:{return 7 from outer;0},}else{a:0,},};')]
        for name, tail in returns:
            for cycle in ('self', 'mutual', 'three'):
                # All declaration orders for the original completed-member case.
                orders = ('helpers', 'reverse', 'export') if name == 'selected' and cycle == 'mutual' else ('helpers',)
                call = 'stop(n-1);' if cycle == 'self' else 'mid(n-1);'
                decls = ['recursive fn stop(n:i64){if n>0 {' + call + '}else{' + tail + '}}']
                if cycle != 'self':
                    decls += ['recursive fn mid(n:i64){' + ('last(n);' if cycle == 'three' else 'stop(n);') + '}']
                if cycle == 'three':
                    decls += ['recursive fn last(n:i64){stop(n);}']
                for order in orders:
                    outer = 'export fn outer()->i64{stop(3);0}'
                    declarations = list(reversed(decls)) if order == 'reverse' else decls
                    text = '\n'.join(([outer, *declarations] if order == 'export' else [*declarations, outer]))
                    if name == 'constructor':
                        text = 'struct S{a:i64}\n' + text
                    for level in ('-O0', '-O2'):
                        for flag in ('false', 'true', 'false'):
                            definitions = ['--define', 'CALL=' + flag]
                            source.write_text(text + '\nfn main(){}')
                            invoke(['check', level, *definitions, source])
                            source.write_text(text)
                            invoke([level, *definitions, '--standalone', '--header', header, source, '-o', cfile])
                            host(7 if flag == 'true' else 0)

        # Preserve an older live cache entry across a deferred attempt; also
        # discard a completed nonrecursive callee tied to the deferred caller.
        adjacent = [
            ('recursive fn ready(n:i64)->i64{if n>0{ready(n-1)}else{1}} '
             'recursive fn stop(n:i64){let x=ready(1);if n>0{mid(n-1);}else{'
             'const if build::CALL{return 7 from outer;}}} '
             'recursive fn mid(n:i64){stop(n);} export fn outer()->i64{stop(3);0}',
             'fn main(){print(ready(2));}'),
            ('fn prior(b:bool){if b{return 2 from stop;}} '
             'fn stop()->i64{prior(false);const if build::CALL{return 7 from outer;} 0} '
             'export fn outer()->i64{stop();0}', 'fn main(){}')]
        for text, main in adjacent:
            for level in ('-O0', '-O2'):
                for flag in ('false', 'true', 'false'):
                    definitions = ['--define', 'CALL=' + flag]
                    source.write_text(text + main)
                    invoke(['check', level, *definitions, source])
                    source.write_text(text)
                    invoke([level, *definitions, '--standalone', '--header', header, source, '-o', cfile])
                    host(7 if flag == 'true' else 0)

    invalid = [
        ('fn unused(){api();}', 'const if true{return 7 from outer;}'),
        ('fn unused(){bridge();} fn bridge(){bridge2();} fn bridge2(){api();}',
         'const if true{return 7 from outer;}'),
        ('fn unused(){api();} fn stop(){const if true{return 7 from outer;}}', 'stop();0'),
        ('fn unused(){api();}', 'const if true{return 7 from missing;}'),
        ('fn unused(){api();}', 'const for <C> in [false,true]{const if C{return 7 from outer;}} 0'),
        ('fn unused(){api();} recursive fn stop(n:i64){if n>0{mid(n-1);}else{const if true{return 7 from outer;}}}'
         'recursive fn mid(n:i64){stop(n);}', 'stop(3);0'),
    ]
    if not core_only and not fields_only:
        invalid += [('struct S{a:i64} fn unused(){api();}',
                     'let s=S{const if true{a:{return 7 from outer;0},},};s.a')]
    for prefix, body in invalid:
        for earlier in (False, True):
            source.write_text(prefix + ' export fn api()->i64{' + body + '}'
                              'fn outer()->i64{0} fn main(){' + ('unrelated();' if earlier else '') + '}')
            for level in ('-O0', '-O2'):
                for args in (['check', level, source], [level, source, '-o', cfile]):
                    p = invoke(args, ok=False)
                    assert ('return from ' in p.stderr or 'export fn api:' in p.stderr), p.stderr
                    assert ('unknown function: unrelated' in p.stderr) == earlier, p.stderr

    # One deferred export's error cannot stand in for another one's error.
    source.write_text('fn unused1(){one();} fn unused2(){two();}\n'
                      'export fn one()->i64{const if true{return 1 from target1;}}\n'
                      'export fn two()->i64{const if true{return 2 from target2;}}\n'
                      'fn target1()->i64{0} fn target2()->i64{0} fn main(){}')
    for level in ('-O0', '-O2'):
        p = invoke(['check', level, source], ok=False)
        assert 'return from target1' in p.stderr or 'export fn one:' in p.stderr, p.stderr
        assert 'return from target2' in p.stderr or 'export fn two:' in p.stderr, p.stderr

    # Editor recovery must report both roots, then retain just the selected one.
    text = ('fn unused(){api();}\nexport fn api()->i64{const if true{return 7 from outer;}else{0}}\n'
            'fn outer()->i64{0}\nfn main(){unrelated();}\n')
    source.write_text(text)
    for level in ('-O0', '-O2'):
        p = invoke(['check', level, '--diagnostics', 'json', source], ok=False)
        messages = '\n'.join(d['message'] for d in json.loads(p.stdout))
        assert 'unknown function: unrelated' in messages, messages
        assert 'return from ' in messages or 'export fn api:' in messages, messages
    uri = source.as_uri()
    client = Client(str(exe), root)
    try:
        client.request('initialize', {'processId': None, 'rootUri': root.as_uri(), 'capabilities': {},
                                     'initializationOptions': {'entryFiles': [str(source)]}})
        client.send('initialized', {}, request=False)
        client.send('textDocument/didOpen', {'textDocument': {'uri': uri, 'languageId': 'goose',
                                                            'version': 1, 'text': text}}, request=False)
        for version, changed, unrelated, foreign in [
                (1, text, True, True), (2, text.replace('unrelated();', ''), False, True),
                (3, text.replace('const if true', 'const if false'), True, False)]:
            if version > 1:
                client.send('textDocument/didChange', {'textDocument': {'uri': uri, 'version': version},
                                                      'contentChanges': [{'text': changed}]}, request=False)
            ds = client.diagnostics_for(uri)
            messages = '\n'.join(d['message'] for d in ds)
            assert ('unknown function: unrelated' in messages) == unrelated, ds
            assert ('return from ' in messages or 'export fn api:' in messages) == foreign, ds
            checks += 1
        client.request('shutdown', {})
        client.send('exit', {}, request=False)
        assert client.p.wait(timeout=10) == 0
    finally:
        if client.p.poll() is None:
            client.p.kill()
            client.p.wait()
    return checks


if __name__ == '__main__':
    with tempfile.TemporaryDirectory(prefix='goose-const-if-transactions-') as directory:
        count = check_transactions(pathlib.Path(sys.argv[1]).resolve(), pathlib.Path(directory),
                                   '--core-only' in sys.argv, '--fields-only' in sys.argv,
                                   '--diagnostics-only' in sys.argv)
        print(f'const if transactions: {count} checks passed')
