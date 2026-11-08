#!/usr/bin/env python3
"""Flat record snapshots: independent fixtures, rejection and generated-C guards."""
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


def check(exe=None):
    exe = exe or os.environ.get('GOOSE_TEST_EXE') or shutil.which('goose++')
    checks = 0
    with tempfile.TemporaryDirectory(prefix='goose-record-read-') as td:
        root = Path(td)
        env = dict(os.environ, GOOSE_HOME=str(root/'home'))
        def run(args, success=True):
            p = subprocess.run(list(map(str,args)), env=env, capture_output=True,
                               text=True, timeout=120)
            assert (p.returncode == 0) == success, (args,p.stdout,p.stderr)
            return p.stdout + p.stderr
        source, c = root/'record.goose', root/'record.c'
        # --parse deliberately accepts ordinary declarations and calls:
        # eligibility is semantic, unlike the packed-word u128 grammar error.
        cases = [
            ('struct R {}', 'R', 'nonempty'),
            ('', 'u32', 'ordinary struct'),
            ('root struct R { x:u8 }', 'R', 'root structs'),
            ('struct R<T> { x:T }', 'R<u8>', 'generic structs'),
            ('struct R { x:u8 }', 'const R', 'unqualified ordinary struct'),
            ('struct R { x:u8 }', 'R&', 'unqualified ordinary struct'),
            ('packed word R:u8 {x:u8}', 'R', 'ordinary struct'),
            ('struct R {pad 1,x:u8}', 'R', 'padding'),
            ('struct R {pad,x:u8}', 'R', 'padding'),
            ('struct R {x:u8=3}', 'R', 'field defaults'),
            ('struct R {let x:u8}', 'R', 'writable fields'),
            ('struct R {x:const u8}', 'R', 'unqualified writable'),
        ]
        for field in ('bool','f32','f64','u8[2]','u8[:]','u8&','varint',
                      'Inner','E','W','UnsafePtr'):
            cases.append(('struct Inner{x:u8} enum E{A} packed word W:u8{x:u8} '
                          f'struct R{{x:{field}}}', 'R', 'must be u8/'))
        cases += [('var table:u8[>..]=[]; struct R{x:u32 in table}', 'R', 'must be u8/')]
        cases += [('struct R{const if build::DEBUG {x:u8} else {x:u16}}',
                   'R','conditional fields')]
        for decl, typ, message in cases:
            source.write_text(decl+f' fn main(){{let r,ok=read_record_le<{typ}>(0,"abc");}}')
            for debug in ('true','false') if 'build::DEBUG' in decl else ('true',):
                for options in (['--check'],['--parse'],['-O0','-o',c],['-O2','-o',c]):
                    parse = options == ['--parse']
                    out = run([exe,'-D',f'DEBUG={debug}',*options,source],parse)
                    if not parse:
                        assert message in out, (decl,out)
                        assert out.count('error:') == 1, out
                    assert not c.exists()
                    checks += 1
        # Argument kinds, type arity and scalar position are checked normally.
        for call in ('read_record_le(0,"x")','read_record_le<R,R>(0,"x")',
                     'read_record_le<R>(false,"x")','read_record_le<R>(0,1)',
                     'read_record_le<R>(0,unsafe_ptr_from_handle(0))',
                     'read_record_le<R>(0,1,2)'):
            source.write_text('struct R{x:u8} fn main(){let r,ok='+call+';}')
            run([exe,'--check',source],False)
            checks += 1

        declarations, body, expected = [], [], []
        def output(expr, value):
            body.append('print('+expr+');')
            expected.append(str(value).lower())
        def layout(name, types):
            declarations.append('struct '+name+'{'+','.join(
                f'f{i}:{t}' for i,t in enumerate(types))+'}')
        kinds = ['u8','u16','u32','u64','i8','i16','i32','i64']
        layout('Mixed', kinds)
        declarations.append('type Byte = u8; type Count = u32; struct Aliased{x:Byte,y:Count}')
        # Edge patterns for each scalar kind for unsigned and signed conversions,
        # using an independent Python little-endian oracle, at unaligned 1.
        for i,typ in enumerate(kinds):
            layout('Scalar'+str(i), [typ])
            width=int(typ[1:])//8
            for bits in (0,1,(1<<(width*8-1))-1,1<<(width*8-1),(1<<(width*8))-1):
                data=[91]+list(bits.to_bytes(width,'little'))
                name=f's{i}_{bits}'
                body.append('let bytes'+name+':u8['+str(len(data))+']=['+','.join(map(str,data))+'];')
                body.append('let '+name+',ok'+name+'=read_record_le<Scalar'+str(i)+'>(1,bytes'+name+');')
                output('ok'+name, True)
                value=int.from_bytes(bytes(data[1:]),'little',signed=typ[0]=='i')
                output(name+'.f0',value)
        # The three production shapes: 10*u32+2*u8; 13*u32+7*i64+3*u32; u64,u64,u32.
        shapes={'Signature':['u32']*10+['u8']*2,
                'Metadata':['u32']*13+['i64']*7+['u32']*3,
                'Memory':['u64','u64','u32'], 'Mixed':kinds}
        for name,types in shapes.items():
            if name!='Mixed': layout(name,types)
            n=sum(int(t[1:])//8 for t in types)
            assert name not in ('Signature','Metadata','Memory') or n=={
                'Signature':42,'Metadata':120,'Memory':20}[name]
            data=bytes((i*37+129)%256 for i in range(n+1))
            body.append(f'var data{name}:u8[{n+1}]=['+','.join(map(str,data))+'];')
            for at,length in ((0,0),(0,n-1),(0,n),(1,n+1),(2,n+1),
                              (0,n+1),(-1,n+1),(n+1,n+1),(n+2,n+1),
                              (-9223372036854775808,n+1),(9223372036854775807,n+1)):
                tag=f'r{len(expected)}'
                body.append(f'let {tag},ok{tag}=read_record_le<{name}>({at},data{name}[0..{length}]);')
                good=0<=at<=length and n<=length-at
                output('ok'+tag,good)
                offset=at
                for i,t in enumerate(types):
                    width=int(t[1:])//8
                    value=int.from_bytes(data[offset:offset+width],'little',signed=t[0]=='i') if good else 0
                    output(tag+f'.f{i}',value)
                    offset+=width
            # Decode never changes the input or its neighboring byte.
            for i,value in enumerate(data): output(f'data{name}[{i}]',value)
        declarations += [
            'struct Pair {a:u32,b:u16}',
            'fn decode(at:i64,data:const u8[:])->Pair,bool {return read_record_le<Pair>(at,data);}',
            'fn index(data:const u8[:],at:i64)->u8 {data[at]}',
            'fn position(count:i64&,data:u8[>..<]&)->i64 {count=count*10+1; data.resize(6,7); 0}',
            'fn buffer(count:i64&,data:const u8[:])->const u8[:] {count=count*10+2; data}',
            'struct Box{value:Pair}',
        ]
        body += ['var count:i64=0; var grow:u8[>..<]=[];',
                 'var pair,ok=decode(position(count,grow),buffer(count,grow));']
        output('count',12); output('ok',True); output('pair.a',117901063)
        body += ['grow[0]=1; let box=Box{pair}; pair.b=9;']
        output('box.value.b',1799); output('grow[4]',7)
        # The destination old bytes are a valid source until all reads finish.
        body += ['var destination:Pair[1]=[pair]; destination[0],ok=read_record_le<Pair>(0,bytes_of(destination)); pair=destination[0];']
        output('ok',True); output('pair.a',117901063); output('pair.b',9)
        body += ['let alias,aliasok=read_record_le<Aliased>(0,"abcde");']
        output('aliasok',True); output('alias.x',97); output('alias.y',1701077858)
        source.write_text('\n'.join(declarations)+'\nfn main(){\n'+'\n'.join(body)+'\n}')
        for options in (['--parse'],['--check','--roundtrip']):
            run([exe,*options,source]); checks+=1
        for level in (0,2):
            run([exe,f'-O{level}','--standalone','-o',c,source])
            for cc in (os.environ.get('CC','gcc'),os.environ.get('CLANG','clang')):
                binary=root/'record'
                run([cc,'-std=c11',f'-O{level}','-fsanitize=undefined',
                     '-fno-sanitize-recover=all',c,'-lm','-pthread','-ldl','-o',binary])
                actual=run([binary]).splitlines()
                assert actual==expected, (level,cc,[(i,a,b) for i,(a,b) in
                    enumerate(zip(actual,expected)) if a!=b][:10],len(actual),len(expected))
                checks+=len(expected)
        # Pure buffer JIT smoke includes signed extremes and fresh-result aliasing.
        actual=run([exe,source]).splitlines()
        assert actual==expected
        checks+=len(expected)
        # Inspect runtime-position/length decoding independently of main's constants.
        source.write_text('struct Pair{a:u32,b:i16} '
            'fn decode(at:i64,data:const u8[:])->Pair,bool {return read_record_le<Pair>(at,data);} '
            'export fn index(at:i64,data:const u8[:])->u8 {data[at]} '
            'fn main(){print(decode(0,"abcdef")); print(index(1,"abc"));}')
        for level in (0,2):
            run([exe,f'-O{level}','--standalone','-o',c,source])
            text=c.read_text()
            # Function bodies, excluding prototypes and the embedded runtime.
            decode=re.search(r'\n[^\n;]*decode_g[^\n;]*\{(.*?)\n}',text,re.S)
            assert decode, text[-10000:]
            code=decode[1]
            assert len(re.findall(r'if \([^\n]*<=.*&&.*<=',code))==1,code
            before,after=code.split('if (',1)
            assert not re.search(r'\.data\s*\+|\[\d+\]',before),before
            assert 'GS_IDX' not in code and 'gs_abort' not in code,code
            assert 'const uint8_t *' in after and '[5]' in after,after
            index=re.search(r'\n[^\n;]*index_g[^\n;]*\{(.*?)\n}',text,re.S)
            assert index and 'GS_IDX' in index[1],text[-10000:]
            checks+=5
    print(f'record read: {checks} checks passed')
    return checks

if __name__=='__main__':
    check()
