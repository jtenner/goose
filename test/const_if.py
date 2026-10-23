#!/usr/bin/env python3
"""Native const-if acceptance: python test/const_if.py path/to/goose [--core-only].

Uses fresh processes and alternating definitions to catch configuration leakage;
checks emitted C as well as executions, so -O0 cannot hide runtime-only pruning.
"""
import pathlib
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'scripts'))
from lsp_protocol import Client

EXE = pathlib.Path(sys.argv[1]).resolve()
CORE_ONLY = '--core-only' in sys.argv[2:]
FIELDS_ONLY = '--fields-only' in sys.argv[2:]
CHECKS = 0


def invoke(args, *, ok=True, contains=None):
    global CHECKS
    p = subprocess.run([str(EXE), *map(str, args)], capture_output=True, text=True, timeout=90)
    text = p.stdout + p.stderr
    assert (p.returncode == 0) == ok, (args, p.returncode, text[-6000:])
    if contains:
        assert contains in text, (args, contains, text[-6000:])
    CHECKS += 1
    return p


CORE = '''
let ENABLED = !false && (3 * 2 == 6);
let BYTEMAX: u8 = 255;
let POSITIVE: i64 = 1;
let LARGE: u64 = 18446744073709551615;
let EXCLUDED_MESSAGE = "excluded_global_data_sentinel";
let C = 1;
fn match_selected() {
    match 0 {
        const for <C> in [0, 1] { C => const if C == 0 { 7 } else { 9 }, },
        _ => 11,
    }
}
fn move_result() -> i64[>..] {
    var a: i64[>..] = [1, 2, 3];
    const if true { a } else { a }
}
fn move_inner() -> i64[>..] { const if true { var a: i64[>..] = [1, 2, 3]; a } }
export fn api() -> i64 { const if false { return 1 from outside; } else { 7 } }
enum Mode { Ok }
type Number = u32;
fn excluded_call() { print("excluded_call_sentinel"); }
fn stopped(b: bool) { if b { return; const if MISSING {} } else {} }
fn chosen<T>(x: T) -> T {
    const if ENABLED && build::COUNT >= 2 { x } else { missing(x); }
}
fn main() {
    const if build::DEBUG {
        print("debug");
    } else {
        const if !build::DEBUG || false { print("release"); }
        else { let bad: ns::Unknown = ns::Unknown {}; }
    }
    const if false {
        excluded_call();
        print(EXCLUDED_MESSAGE);
        let bad: ns::Unknown = ns::Unknown {};
        let e: Mode.Missing = Mode.Missing {};
        let badalias: Number<ns::Missing> = 1;
        fn nested(v: ns::Missing) { unknown(); }
    } else { let local = 5; print(local); }
    const if false {} else {}
    print(chosen(9));
    stopped(true);
    assert(match_selected() == 7);
    let moved = move_result();
    assert(moved.len == 3);
    let inner = move_inner();
    assert(inner.len == 3);
    const if !(1 < 2 && 2 <= 2 && 3 > 2 && 3 >= 3 && true != false && !false == true) { unknown(); }
    const if POSITIVE < LARGE {} else { unknown(); }
    const if ~0 == BYTEMAX { } else { unknown(); }
    const for <C> in [1, 2] { const if C == 1 {} else {} }
    const for <N> in ["keep", "drop"] { const if N == "keep" {} else {} }
    const if true {} else if false { unknown(); } else { unknown(); }
    const for <N> in [true, false] {
        const if N { print("yes"); } else { print("no"); }
    }
    const for <T> in types<u32, u64> {
        const if build::DEBUG { let x: T = 3; print(x); }
        else { let x: T = 4; print(x); }
    }
    if build::DEBUG { print("ordinary"); } else { print("normal"); }
}
'''

FIELDS = '''
let EXTRA = build::DEBUG && (build::COUNT + 1 == 3);
struct S<T> {
    a: u32 = 1,
    const if EXTRA { let b: u64 = 2, } else {},
    z: T = 3,
}
struct Empty { const if false { bad: ns::Unknown, } else {}, }
struct Padded {
    a: u8 = 1,
    const if build::DEBUG { pad 4, const b: u32 = 2, } else { pad 2, },
    z: u8 = 3,
}
fn show<T>(x: T) {
    const for <N, A> in fields<T> { print(N, "=", x.A); }
}
fn main() {
    let x = S<u32> {};
    show(x);
    let values = [x];
    let image = bytes_of(values);
    // Size and offsets are an application layout fingerprint, independent
    // of natural alignment: z starts at 4 (release) or 12 (debug).
    print(image.len, " ", image[0], " ", image[4], " ", image[image.len - 4]);
    let p = Padded {};
    print(bytes_of([p]).len);
    let empty: Empty[2] = [Empty {}, Empty {}];
    print(bytes_of(empty).len);
}
'''

CONSTRUCTORS = '''
struct S { a: u32, const if build::DEBUG { b: u64 = 8, } else {}, z: u32 = 3 }
fn main() {
    let a = S { a: 1, const if build::DEBUG { b: 2, } else {}, z: 4 };
    let b = S { 1, const if build::DEBUG { 2, } else {}, 4 };
    print(a == b);
    let c = S { a: 1, const if false { unknown: missing(), } else {}, };
    print(c.z);
    const for <K> in [true, false] {
        let d = S { a: 1, const if K { z: 7, } else { z: 9, }, };
        print(d.z);
    }
    let e = S { const if build::DEBUG { a: 2, } else { 2, }, .. };
    print(e.a);
}
'''

with tempfile.TemporaryDirectory(prefix='goose-const-if-') as directory:
    root = pathlib.Path(directory)
    source, cfile = root / 'main.goose', root / 'main.c'
    for level in ('-O0', '-O2'):
        for debug in ('false', 'true', 'false'):
            definitions = ['--define', 'DEBUG=' + debug, '--define', 'COUNT=2']
            cases = [(CORE, ('debug' if debug == 'true' else 'release') + '\n5\n9\nyes\nno\n' +
                      ('3\n3\nordinary\n' if debug == 'true' else '4\n4\nnormal\n'))]
            if not CORE_ONLY:
                cases += [(FIELDS, 'a=1\n' + ('b=2\n' if debug == 'true' else '') + 'z=3\n' +
                           ('16 1 2 3\n10\n2\n' if debug == 'true' else '8 1 3 3\n4\n2\n')),
                          (CONSTRUCTORS, 'true\n3\n7\n9\n2\n')]
            if FIELDS_ONLY:
                cases = cases[:2]
            for code, expected in cases:
                source.write_text(code)
                invoke(['check', '--roundtrip', level, *definitions, source])
                # Parse-level dump retains both arms and reparses unchanged.
                dump = invoke(['--dump', source]).stdout
                dumped = root / 'dumped.goose'
                dumped.write_text(dump)
                assert invoke(['--dump', dumped]).stdout == dump
                result = invoke(['run', level, *definitions, source])
                assert result.stdout == expected, (expected, result.stdout)
                invoke([level, *definitions, source, '-o', cfile])
                native = root / 'native'
                invoke(['build', level, *definitions, source, '-o', native])
                execution = subprocess.run([str(native)], capture_output=True, text=True, timeout=30)
                assert execution.returncode == 0 and execution.stdout == expected, execution
                # Separate ASTs in one compiler process reuse the same config.
                invoke(['--multi-test', '--check', *definitions, source, source])
                c = cfile.read_text()
                assert 'excluded_global_data_sentinel' not in c
                assert 'excluded_call_sentinel' not in c and 'excluded_call(' not in c
                assert 'ns_Unknown' not in c and 'ns_Missing' not in c

    failures = [
        ('fn main() { const if MISSING {} }', 'const if'),
        ('fn main() { const if 1 {} }', 'bool'),
        ('fn f() -> bool { true } fn main() { const if f() {} }', 'constant'),
        ('var X = true; fn main() { const if X {} }', 'constant'),
        ('let X = true; fn main() { let X = false; const if X {} }', 'local'),
        ('let X = true; fn f(X: bool) { const if X {} } fn main() { f(true); }', 'local'),
        ('fn main() { const if true { let inside = 1; } print(inside); }', 'inside'),
        ('fn main() { const if false { let bad: = ; } }', None),
        ('fn main() { const if false { let bad = (1 + ); } }', None),
        ('fn main() { const if true { let bad: ns::Unknown = ns::Unknown {}; } }', 'unknown type'),
        ('enum E { A } fn main() { const if true { let bad: E.Missing = E.Missing {}; } }', 'variant'),
        ('fn main() { const if true || MISSING {} }', 'constant'),
        ('fn main() { const if false && 4 {} }', 'bool'),
        ('fn unused() { const if false { return from missing; } else { unrelated(); } } fn main() {}', 'unrelated'),
        ('let N = 2; fn main() { const if true { fn inner<N>(x: u8[N]) {} } }', 'type parameter'),
        ('let FLAG = true; fn f() -> i64 { { let FLAG = false; const if FLAG { 1 } else { 2 } } } fn main() { print(f()); }', 'local'),
        ('let FLAG = true; fn main() { if true { let FLAG = false; const if FLAG {} } else {} }', 'local'),
        ('let N = 2; fn main() { const if true { fn inner(N: i64, x: u8[N]) {} } }', 'parameter'),
    ]
    if not CORE_ONLY:
        failures += [
            ('struct S { a: u32, const if true { a: u32, } } fn main() {}', 'duplicate field'),
            ('struct S { const if MISSING { a: u32, } } fn main() {}', 'const if'),
            ('struct S<T> { const if T { a: u32, } } fn main() {}', 'type parameter'),
            ('struct S { const if false { a: ns::Unknown, } } fn main() { let s = S {}; print(s.a); }', 'a'),
            ('struct S { const if false { a: , } } fn main() {}', None),
            ('struct S { a: u32 } fn main() { let s = S { a: 1, const if true { a: 2, }, }; }', 'duplicate'),
            ('struct S { a: u32, b: u32 } fn main() { let s = S { a: 1, const if true { 2, }, }; }', 'mix'),
            ('struct S { a: u32 } fn main() { let s = S { const if false { a: 1, }, }; }', 'missing'),
            ('struct S { a: u32 } fn main() { let s = S { const if true { absent: 1, }, }; }', 'field'),
        ]
    if FIELDS_ONLY:
        failures = failures[:-4]
    for code, diagnostic in failures:
        source.write_text(code)
        invoke(['check', source], ok=False, contains=diagnostic)

    source.write_text('fn main() { missing(); } fn later() { const if true { other(); } }')
    recovery = invoke(['check', source], ok=False)
    assert 'unknown function: missing' in recovery.stderr and 'unknown function: other' in recovery.stderr, recovery.stderr

    if not CORE_ONLY:
        # Excluded names remain quiet in editor analysis; malformed excluded
        # syntax still reports, and a subsequent edit recovers selected fields.
        text = ("fn unused<T>(v: T) { const if true { let x: ns::Missing = ns::Missing {}; } }\n"
                "struct S { const if build::DEBUG { enabled: u32 = 1, } "
                "else { disabled: u32 = 2, } }\n"
                "fn main() { const if build::DEBUG { let bad: ns::Unknown = ns::Unknown {}; } "
                "else { let x = S {}; print(x.disabled); } }\n")
        source.write_text(text)
        uri = source.as_uri()
        client = Client(str(EXE), root, ['--define', 'DEBUG=false'])
        try:
            client.request('initialize', {'processId': None, 'rootUri': root.as_uri(), 'capabilities': {},
                                         'initializationOptions': {'entryFiles': [str(source)]}})
            client.send('initialized', {}, request=False)
            client.send('textDocument/didOpen', {'textDocument': {'uri': uri, 'languageId': 'goose',
                                                                'version': 1, 'text': text}}, request=False)
            diagnostics = client.diagnostics_for(uri)
            assert diagnostics == [], diagnostics
            position = {'line': 2, 'character': text.splitlines()[2].index('x.disabled') + 2}
            doc = {'textDocument': {'uri': uri}, 'position': position}
            items = client.request('textDocument/completion', doc)['items']
            labels = [item['label'] for item in items]
            assert 'disabled' in labels and 'enabled' not in labels, labels
            broken = text.replace('let bad: ns::Unknown', 'let bad:')
            for version, changed, expect_error in ((2, broken, True), (3, text, False)):
                client.send('textDocument/didChange', {'textDocument': {'uri': uri, 'version': version},
                                                      'contentChanges': [{'text': changed}]}, request=False)
                diagnostics = client.diagnostics_for(uri, accept=lambda ds: bool(ds) == expect_error)
                assert bool(diagnostics) == expect_error, diagnostics
            client.request('shutdown', {})
            client.send('exit', {}, request=False)
            assert client.p.wait(timeout=10) == 0
            CHECKS += 4
        finally:
            if client.p.poll() is None:
                client.p.kill()
                client.p.wait()

print(f'const if: {CHECKS} checks passed')
