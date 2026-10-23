"""Persistent variable obligations belong to surviving root transactions."""
import json
import pathlib
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'scripts'))
from lsp_protocol import Client


def check_marks(exe, root, core_only=False, fields_only=False):
    checks = 0

    def invoke(args, ok=True):
        nonlocal checks
        p = subprocess.run([str(exe), *map(str, args)], capture_output=True, text=True, timeout=90)
        assert p.returncode >= 0, (args, p.returncode, p.stderr[-4000:])
        assert (p.returncode == 0) == ok, (args, p.returncode, p.stderr[-4000:])
        checks += 1
        return p

    boolean = 'let FLAG=true;\n'
    integers = 'let N:i64=1;let U:u64=18446744073709551615;\n'
    tail = 'const if true{return 7 from outer;}'
    cases = [
        ('refwrite', boolean, 'fn stop(){let r=&FLAG;' + tail + '}', 'const if FLAG{1}else{2}'),
        ('constuse', boolean, 'fn stop(){const if FLAG{}' + tail + '}', 'let r=&FLAG;1'),
        ('nonneguse', integers, 'fn stop(){print(N<U);' + tail + '}', 'let r=&N;1'),
        ('generic', boolean, 'fn touch<T>(){let r=&FLAG;} fn stop(){touch<u8>();' + tail + '}',
         'const if FLAG{1}else{2}'),
        ('nested', boolean, 'fn stop(){const if true{fn touch(){let r=&FLAG;} touch();}' + tail + '}',
         'const if FLAG{1}else{2}'),
        ('recursive', boolean, 'recursive fn touch<T>(n:i64){let r=&FLAG;if n>0{touch<T>(n-1);}}'
         'fn stop(){touch<u8>(2);' + tail + '}', 'const if FLAG{1}else{2}'),
        ('constfor', boolean, 'fn stop(){const for <C> in [false,true]{const if C{let r=&FLAG;'
         'return 7 from outer;}}}', 'const if FLAG{1}else{2}'),
        ('extentuse', 'let A="ab";\n',
         'fn stop(){let a:u8[A.len]=[0,0];' + tail + '}', 'A.len-1'),
        ('generic_write', boolean, 'fn touch<T>(){let r=&FLAG;r=false;}'
         'fn stop(){touch<u8>();' + tail + '}', 'const if FLAG{1}else{2}'),
        ('param_default', boolean, 'fn touch<T>(v:bool={let r=&FLAG;false}){}'
         'fn stop(){touch<u8>();' + tail + '}', 'const if FLAG{1}else{2}'),
        ('struct_default', boolean + 'struct Defaults<T>{v:bool={let r=&FLAG;false}}\n',
         'fn stop(){let s=Defaults<u8>{};' + tail + '}', 'const if FLAG{1}else{2}'),
    ]
    if not core_only and not fields_only:
        cases += [('constructor', boolean + 'struct S{a:i64}\n',
                   'fn stop(){let s=S{const if true{a:{let r=&FLAG;return 7 from outer;0},},};}',
                   'const if FLAG{1}else{2}')]
    source, cfile, header = root / 'marks.goose', root / 'marks.c', root / 'marks.h'
    # The VarDef pointer can remain unchanged while its pending array's shared
    # element type is mutated. A discarded inference must not pick the live type.
    pending = ('var DATA=[];fn stop(){DATA.push("x");' + tail + '}\n'
               'fn outer()->i64{0}export fn api()->i64{DATA.push(1);1}')
    for level in ('-O0', '-O2'):
        source.write_text(pending + 'fn main(){}')
        invoke(['check', level, source])
        source.write_text(pending)
        invoke([level, '--standalone', '--header', header, source, '-o', cfile])

    # A retained type cache must not outlive the proof obligations its layout
    # used. Test both unused and reused instances, and both declaration orders.
    for declaration, literal in [('struct Box<T>{a:T[N]}', 'Box<u8>{[1,2]}'),
                                 ('enum Box<T>{V{a:T[N]}}', 'Box<u8>.V{[1,2]}'),
                                 ('struct Box<T>{a:u8[N]}', 'Box<u8>{[1,2]}')]:
        for live in (False, True):
            for ordinary in (False, True):
                helper = ('fn touch<T>(){let s=' + literal + ';}'
                          'fn stop(){touch<u8>();' + (tail.replace('const if', 'if') if ordinary else tail) + '}')
                for order in (False, True):
                    api = 'export fn api()->i64{' + ('let s=' + literal + ';' if live else '') + 'let r=&N;1}'
                    text = 'let N=2;' + declaration + (api + helper if order else helper + api) + 'fn outer()->i64{0}'
                    for level in ('-O0', '-O2'):
                        source.write_text(text + 'fn main(){}')
                        p = invoke(['check', level, source], ok=not live)
                        if live:
                            assert 'writable reference' in p.stderr, p.stderr
                        source.write_text(text)
                        p = invoke([level, '--standalone', '--header', header, source, '-o', cfile], ok=not live)
                        if live:
                            assert 'writable reference' in p.stderr, p.stderr
    for name, globals_, helper, api in cases:
        text = globals_ + helper + '\nfn outer()->i64{0}\nexport fn api()->i64{' + api + '}\n'
        for level in ('-O0', '-O2'):
            source.write_text(text + 'fn main(){}')
            invoke(['check', level, source])
            source.write_text(text)
            invoke([level, '--standalone', '--header', header, source, '-o', cfile])
            host, native = root / 'marks-host.c', root / 'marks-host'
            host.write_text('#include "marks.h"\nint main(int argc,char **argv){goose_init(argc,argv);'
                            'return api()==1?0:1;}\n')
            p = subprocess.run(['cc', level, str(cfile), str(host), '-o', str(native), '-lm', '-pthread'],
                               capture_output=True, text=True, timeout=90)
            assert p.returncode == 0, (name, p.stderr)
            p = subprocess.run([str(native)], capture_output=True, text=True, timeout=10)
            assert p.returncode == 0, (name, p.returncode, p.stderr)
            checks += 1
            # These are genuine live obligations once outer actually calls stop.
            if name != 'extentuse':
                source.write_text(text.replace('fn outer()->i64{0}', 'fn outer()->i64{stop();0}') +
                                  'fn main(){print(outer());}')
                p = invoke(['check', level, source], ok=False)
                assert 'writable reference' in p.stderr, (name, p.stderr)

    # Rollback must restore an earlier obligation, never clear the whole set.
    preexisting = [
        (boolean, 'const if FLAG{}', 'const if FLAG{}', 'let r=&FLAG;1'),
        (boolean, 'let r=&FLAG;', 'let r=&FLAG;', 'const if FLAG{1}else{2}'),
        (integers, 'print(N<U);', 'print(N<U);', 'let r=&N;1'),
    ]
    for globals_, live, discarded, api in preexisting:
        text = (globals_ + 'fn stop(){' + discarded + tail + '}\n'
                'fn outer()->i64{0}\nexport fn api()->i64{' + api + '}\n'
                'fn main(){' + live + '}')
        source.write_text(text)
        for level in ('-O0', '-O2'):
            p = invoke(['check', level, source], ok=False)
            assert 'writable reference' in p.stderr, p.stderr
            assert f'{source}:{text.count(chr(10)) + 1}' in p.stderr, p.stderr

    # JSON and editor repair must agree about both discarded and actual writes.
    text = boolean + 'fn stop(){let r=&FLAG;' + tail + '}\nfn outer()->i64{0}\n'
    text += 'export fn api()->i64{const if FLAG{1}else{2}}\nfn main(){}\n'
    source.write_text(text)
    for level in ('-O0', '-O2'):
        p = invoke(['check', level, '--diagnostics', 'json', source])
        assert json.loads(p.stdout) == [], p.stdout
    client = Client(str(exe), root)
    uri = source.as_uri()
    try:
        client.request('initialize', {'processId': None, 'rootUri': root.as_uri(), 'capabilities': {},
                                     'initializationOptions': {'entryFiles': [str(source)]}})
        client.send('initialized', {}, request=False)
        client.send('textDocument/didOpen', {'textDocument': {'uri': uri, 'languageId': 'goose',
                                                            'version': 1, 'text': text}}, request=False)
        actual = text.replace('fn outer()->i64{0}', 'fn outer()->i64{stop();0}').replace(
            'fn main(){}', 'fn main(){print(outer());}')
        for version, changed, bad in [(1, text, False), (2, actual, True), (3, text, False)]:
            if version > 1:
                client.send('textDocument/didChange', {'textDocument': {'uri': uri, 'version': version},
                                                      'contentChanges': [{'text': changed}]}, request=False)
            ds = client.diagnostics_for(uri)
            assert bool(ds) == bad, ds
            if bad:
                assert any('writable reference' in d['message'] for d in ds), ds
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
    with tempfile.TemporaryDirectory(prefix='goose-const-if-marks-') as directory:
        print('const if marks:', check_marks(pathlib.Path(sys.argv[1]).resolve(), pathlib.Path(directory),
                                            '--core-only' in sys.argv, '--fields-only' in sys.argv),
              'checks passed')
