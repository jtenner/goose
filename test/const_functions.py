#!/usr/bin/env python3
"""Scalar compile-time functions, configuration and bounded-evaluation acceptance."""
import json
import pathlib
import re
import subprocess
import sys
import tempfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from lsp_protocol import Client

EXE = pathlib.Path(sys.argv[1]).resolve()
CHECKS = 0
WIDTH = '''
const fn w2(n:u64)->u64 {return if n>1 {2} else {1};}
const fn w4(n:u64)->u64 {return if n>3 {2+w2(n>>2)} else {w2(n)};}
const fn w8(n:u64)->u64 {return if n>15 {4+w4(n>>4)} else {w4(n)};}
const fn w16(n:u64)->u64 {return if n>255 {8+w8(n>>8)} else {w8(n)};}
const fn w32(n:u64)->u64 {return if n>65535 {16+w16(n>>16)} else {w16(n)};}
const fn width64(n:u64)->u64 {return if n>4294967295 {32+w32(n>>32)} else {w32(n)};}
'''


def invoke(args, ok=True, contains=None):
    global CHECKS
    p = subprocess.run([str(EXE), *map(str, args)], capture_output=True, text=True, timeout=120)
    assert (p.returncode == 0) == ok, (args, p.stdout[-2000:], p.stderr[-6000:])
    if contains:
        assert contains in p.stdout+p.stderr, (contains, p.stdout, p.stderr)
    CHECKS += 1
    return p


with tempfile.TemporaryDirectory(prefix='goose-ctf-') as tmp:
    root = pathlib.Path(tmp)
    source = root/'main.goose'
    def check(text, ok=True, contains=None):
        source.write_text(text)
        p=invoke(['check', source], ok, contains)
        if not ok and contains in ('cycle','division by zero','active call limit','visit limit'):
            ds=json.loads(invoke(['check','--diagnostics','json',source],False).stdout)
            assert ds[0]['line']>0 and pathlib.Path(ds[0]['file'])==source,ds
            assert ds[0].get('related'),ds
        return p
    def matrix(text, expected):
        source.write_text(text)
        invoke(['--parse', '--roundtrip', source])
        invoke(['check', source])
        for opt in ['0', '2']:
            c = root/'output.c'
            invoke([f'-O{opt}', '-o', c, source])
            assert not re.search(r'\b(?:w2|w4|w8|w16|w32|width64|needs_edges)\s*\(', c.read_text())
            p = invoke(['run', f'-O{opt}', source])
            assert p.stdout == expected, p.stdout
            native=root/'native'
            invoke(['build',f'-O{opt}',source,'-o',native])
            p=subprocess.run([str(native)],capture_output=True,text=True,check=True)
            assert p.stdout==expected, p.stdout
    for edges in (False, True):
        for paths in (False, True):
            source.write_text('''const fn needs_edges(a:bool,b:bool)->bool{return a||b;}
const NEED:bool=needs_edges(build::E,build::P);
struct Config {const if NEED {enabled:u8,} else {disabled:u64,}}
fn main(){
    let config=Config{const if NEED {enabled:1,} else {disabled:0,}};
    const if NEED {print(config.enabled);} else {print(config.disabled);}
}
''')
            for opt in ['0', '2']:
                definitions = ['--define', f'E={str(edges).lower()}', '--define', f'P={str(paths).lower()}']
                invoke(['check', *definitions, source])
                c = root/'need.c'
                invoke([f'-O{opt}', *definitions, '-o', c, source])
                assert 'needs_edges(' not in c.read_text()
                p=invoke(['run', f'-O{opt}', *definitions, source])
                assert p.stdout == f'{int(edges or paths)}\n'
                native=root/'need-native'
                invoke(['build',f'-O{opt}',*definitions,source,'-o',native])
                p=subprocess.run([str(native)],capture_output=True,text=True,check=True)
                assert p.stdout==f'{int(edges or paths)}\n'
    for maximum, width, extent in [(255,8,2),(1023,10,2),(2047,11,3)]:
        matrix(WIDTH+f'''
const A:u64=width64(1); const B:u64=width64(31); const C:u64=width64({maximum});
const TABLE:u8[3]=[A as u8,B as u8,C as u8];
const SIZE:u64=(A+B+C+7)/8;
struct Record {{data:u8[SIZE]}}
fn main(){{print(TABLE[0]);print(TABLE[1]);print(TABLE[2]);let r=Record{{data:[0;SIZE]}};print(r.data.len);}}
''',f'1\n5\n{width}\n{extent}\n')
    values = sorted(set(range(65536)) | {2**64-1} |
                    {2**i+d for i in range(64) for d in [-1,0,1] if 0 <= 2**i+d < 2**64})
    for start in range(0,len(values),512):
        batch = values[start:start+512]
        text = WIDTH+'\nfn main(){\n'+''.join(
            f'const if width64({n}) == {max(1,n.bit_length())} {{}} else {{missing();}}\n' for n in batch)+'}\n'
        source.write_text(text)
        for opt in ['-O0','-O2']:
            invoke(['check',opt,source])
    print(f'width64 oracle: {len(values)} values')
    matrix('''
const fn n(x:u64)->u64{return x;}
const fn yes(x:bool)->bool{return x;}
struct S {const if yes(true) {a:u8,} else {bad:missing::Type,}}
fn main(){
    let a:u8[n(3)]=[7;n(3)];
    var b:u8[..n(4)]=[1]; b.push(2);
    const for <I> in [n(0),n(1),n(2)] {const if n(I)==I {} else {missing();}}
    match 3 {n(3)=>{},_=>{abort("bad pattern");}}
    let s=S{const if yes(true) {a:9,} else {bad:missing(),}};
    const if yes(false) {let bad:missing::Type=missing();} else {assert(s.a==9);}
    assert(a.len==3 && b.cap==4);
}
''', '')
    check('const fn f(x:u64)->u64{return x;} fn main(){const if false {let x=;}}',False)

    simple='const fn f(x:u64)->u64{return x;}\n'
    for decl in [
        'const fn f(x:i64)->u64{return 1;}',
        'type U=u64; const fn f(x:U)->u64{return 1;}',
        'const fn f(x:const u64)->u64{return 1;}',
        'const fn f(x:u64=1)->u64{return x;}',
        'const fn f<T>(x:u64)->u64{return x;}',
        'const fn f(x:u64)->u64{return -1;}',
        'const fn f(x:u64)->u64{return 18446744073709551616;}',
        'const fn f(x:u64)->u64{return "bad";}',
        'const fn f(x:u64)->u64{return [1];}',
        'const fn f(x:u64)->u64{let a=1;return a;}',
        'const fn f(x:u64)->u64{while true {} return x;}',
        'const fn f(x:u64)->u64{return sizeof<u64>();}',
        'fn g()->u64{return 1;} const fn f(x:u64)->u64{return g();}',
        'const X:u64=1; const fn f(x:u64)->u64{return X;}',
        'const fn f(x:u64)->u64{return build::X;}',
        'const fn f(x:u64)->u64{return if true {1} else {false};}',
        'const fn f(x:u64)->u64{return if true {1} else {missing()};}',
        simple+'fn f(x:bool)->bool{return x;}',
    ]:
        check(decl+'\nfn main(){}',False)
    for expr in ['f(true)','f(-1)','f(1,2)','f()']:
        check(simple+f'const X:u64={expr}; fn main(){{}}',False)
    for context in ['let x=f(1);','let x=[f(1)];','let x=f;','print(f(1));']:
        check(simple+f'fn main(){{{context}}}',False)
    check(simple+'fn wrapper()->u64{return f(1);} fn main(){}',False)
    check(simple+'struct S{x:u64=f(1)} fn main(){let s=S{};print(s.x);}',False)
    check('const fn f(x:bool)->u64{return x;} fn main(){}',False)
    check('const fn f(x:u64)->u64{return x as u64;} fn main(){}',False)
    check('const fn f(x:u64)->u64{return x+true;} fn main(){}',False)
    check('export const fn f(x:u64)->u64{return x;} fn main(){}',False)
    check(simple+'fn main(){const if true {fn f(x:u64)->u64{return x;} const if f(1)==1 {}}}',False)

    check('const fn f(x:u64)->u64{return if x==0 {1} else {1/0};} const X:u64=f(0); fn main(){}')
    check('const fn f(x:u64)->u64{return if x==0 {1} else {1/0};} const X:u64=f(1); fn main(){}',False,'division by zero')
    check('const fn f(x:bool)->bool{return x || (1/0==1);} const X:bool=f(true); fn main(){}',False,'division by zero')
    check('const fn f(x:u64)->u64{return if x==0 {1} else {f(0)};} const X:u64=f(0); fn main(){}')
    check('const fn f(x:u64)->u64{return f(x);} const X:u64=f(1); fn main(){}',False,'cycle')
    check('const fn f(x:u64)->u64{return g(x);} const fn g(x:u64)->u64{return f(x);} const X:u64=f(1); fn main(){}',False,'cycle')
    check(simple+'const A:u64=f(B);const B:u64=f(A);fn main(){}',False,'cycle')
    check(simple+'const X:u64=f(Y);const Y:u64=7;fn main(){}')
    check(simple+'const Y:u64=7;fn main(){let Y=1;const if f(Y)==7 {}}',False,'local')
    check(simple+'fn main(){let f=1;const if f(1)==1 {}}',False,'local')
    for count in [16,17]:
        params=','.join(f'p{i}:u64' for i in range(count))
        check(f'const fn f({params})->u64{{return 1;}} '+('const X:u64=f('+','.join('1' for _ in range(count))+');' if count==16 else '')+'fn main(){}',count==16)
    for depth in [32,33]:
        chain=''.join(f'const fn depth{i}()->u64{{return '+('1' if i==0 else f'depth{i-1}()')+';}\n' for i in range(depth))
        check(chain+f'const X:u64=depth{depth-1}();fn main(){{}}',depth==32,None if depth==32 else 'active call limit')
    tree='const fn f0()->u64{return 1;}\n'+''.join(f'const fn f{i}()->u64{{return f{i-1}()+f{i-1}();}}\n' for i in range(1,12))
    for padding,unary,ok in [(904,True,True),(905,False,True),(905,True,False)]:
        expr='f11()'+'+1'*padding
        if unary: expr='~('+expr+')'
        check(tree+'const X:u64='+expr+';fn main(){}',ok,None if ok else 'visit limit')
    check(tree+'const fn twice(x:u64)->u64{return x+x;} const X:u64=twice(f11());fn main(){}')
    check(tree+simple+'const A:u64=f11();const B:u64=f(A+A);fn main(){}',False,'visit limit')
    check('const fn f(x:bool)->bool{return x && (1/0==1);} const X:bool=f(false); fn main(){}',False,'division by zero')
    for flipped in [False,True,False]:
        body='!x' if flipped else 'x'
        for flag in [True,False]:
            source.write_text(f'const fn pick(x:bool)->bool{{return {body};}} const X:bool=pick(build::FLAG);fn main(){{const if X {{print(1);}} else {{print(0);}}}}')
            defs=['--define',f'FLAG={str(flag).lower()}']
            invoke(['check',*defs,source])
            native=root/'edited-native'
            invoke(['build',*defs,source,'-o',native])
            assert subprocess.check_output([str(native)],text=True)==f'{int(flag != flipped)}\n'

    (root/'helpers.goose').write_text('namespace calc; const fn first(x:u64)->u64{return later(x);} const fn later(x:u64)->u64{return x+1;}')
    check('import helpers;const fn later(x:u64)->u64{return x+99;} const X:u64=calc::first(1);fn main(){const if X==2 {} else {missing();}}')
    check(simple+'const X:u64=f(f(1));fn main(){}')
    check(simple+'const X:u64=f(~0);fn main(){const if X==18446744073709551615 {} else {missing();}}')
    check('const fn f(x:bool)->bool{return if x {false} else {true};} const X:bool=f(false);fn main(){const if X {} else {missing();}}')
    source.write_text(simple+'const X:u64=f(build::N);fn main(){}')
    invoke(['check','--define','N=-1',source],False,'must fit u64')
    invoke(['check','--define','N=18446744073709551615',source])
    for malformed in ['const fn f(x:u64){return x;}',
                      'const fn f(x:u64)->u64{return;}',
                      'const fn f(x:u64)->u64{const if true {return x;}}']:
        check(malformed+'fn main(){}',False)
    source.write_text('const fn fault(x:u64)->u64{\nreturn 1/x;\n}\nconst X:u64=fault(0);\nfn main(){}')
    p=invoke(['check','--diagnostics','json',source],False)
    ds=json.loads(p.stdout)
    assert ds[0]['line']==2, ds
    assert ds[0].get('related'), ds
    for flag in [False,True,False]:
        text='''const fn pick(x:bool)->bool{return x;}
const RESULT:bool=pick(build::FLAG);
fn main(){const if RESULT==build::FLAG {} else {missing();}}
'''
        source.write_text(text)
        client=Client(str(EXE),root,['--define',f'FLAG={str(flag).lower()}'])
        uri=source.as_uri()
        try:
            client.request('initialize',{'processId':None,'rootUri':root.as_uri(),'capabilities':{},
                           'initializationOptions':{'entryFiles':[str(source)]}})
            client.send('initialized',{},request=False)
            client.send('textDocument/didOpen',{'textDocument':{'uri':uri,'languageId':'goose','version':1,'text':text}},request=False)
            assert client.diagnostics_for(uri)==[]
            for version,changed,error in [(2,text.replace('return x','return !x'),True),(3,text,False)]:
                client.send('textDocument/didChange',{'textDocument':{'uri':uri,'version':version},
                            'contentChanges':[{'text':changed}]},request=False)
                ds=client.diagnostics_for(uri,accept=lambda ds:bool(ds)==error)
                assert bool(ds)==error,ds
                CHECKS+=1
            client.request('shutdown',{})
            client.send('exit',{},request=False)
            assert client.p.wait(timeout=10)==0
        finally:
            if client.p.poll() is None:
                client.p.kill();client.p.wait()
print(f'const fn acceptance: {CHECKS} checks passed')
