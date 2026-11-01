#!/usr/bin/env python3
"""Measure scalar ABI and register residency of known-fit u64 leaf kernels."""
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

SOURCE = '''
packed word Header:u64 { _:u3, age:u8, _:u5, kind:u8, _:u40 }
export fn extract(w:Header)->u8 { w.age }
export fn replace(w:Header, value:u8)->Header { var out=w; out.age=value; out }
export fn construct(age:u8, kind:u8)->Header { Header { age,kind } }
export fn equal(a:Header,b:Header)->bool { a==b }
'''
HAND = '''
__attribute__((noinline,used)) uint8_t hand_extract(uint64_t w) { return (w>>3)&255; }
__attribute__((noinline,used)) uint64_t hand_replace(uint64_t w,uint8_t v) { return (w&~(UINT64_C(255)<<3))|((uint64_t)v<<3); }
__attribute__((noinline,used)) uint64_t hand_construct(uint8_t a,uint8_t k) { return ((uint64_t)a<<3)|((uint64_t)k<<16); }
__attribute__((noinline,used)) uint8_t hand_equal(uint64_t a,uint64_t b) { return a==b; }
'''
HOST = '''
#include "api.h"
#include <assert.h>
int main(int argc,char **argv) {
 goose_init(argc,argv);
 uint64_t w=construct(23,42);
 assert(w==((23ULL<<3)|(42ULL<<16)));
 assert(extract(w)==23); assert(extract(replace(w,81))==81);
 assert(equal(w,w)); assert(!equal(w,w|1));
 return 0;
}
'''

def check(exe=None, evidence=None):
    exe=exe or os.environ.get('GOOSE_TEST_EXE') or shutil.which('goose++')
    records=['Packed-word residency evidence (x86-64; measured, not a universal no-spill guarantee).',
             'Goose -O0 --standalone --header; C -std=c11 -O2.',
             'Internal leaf definitions marked noinline,used in the test C; exported wrappers and a separately compiled C host exercise the call boundary.',
             'Handwritten scalar kernels use the same noinline,used attributes.']
    checks=0
    with tempfile.TemporaryDirectory(prefix='packed-residency-') as td:
        p=Path(td); src=p/'kernels.goose'; c=p/'kernels.c'; hdr=p/'api.h'
        src.write_text(SOURCE)
        def run(args):
            r=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=120)
            assert r.returncode==0,(args,r.stderr[:6000])
            return r.stdout
        run([exe,'-O0','--standalone','--header',hdr,'-o',c,src])
        code=c.read_text()
        names=[]
        for name in ('extract','replace','construct','equal'):
            pattern=rf'(?m)^static ([^\n]+) ({name}_g\d*)\(([^\n]*)\) \{{'
            match=re.search(pattern,code)
            assert match,(name,'missing leaf')
            symbol=match[2]; names.append(symbol)
            start=match.end(); end=code.index('\n}',start)
            body=code[start:end]
            assert not any(x in body for x in ('gs_stack','GS_MEMCPY','malloc','&w_g','&out_g')), (name,body)
            assert 'gs_u64' in match[0] or 'uint64_t' in match[0],match[0]
            records.append('\nC leaf: '+match[0]+'\n'+body+'\n}')
            code=code[:match.start()]+'__attribute__((noinline,used)) '+code[match.start():]
            checks+=1
        c.write_text(code+HAND)
        host=p/'host.c'; host.write_text(HOST)
        for cc in (os.environ.get('CC','gcc'),os.environ.get('CLANG','clang')):
            records.append('\nCompiler: '+run([cc,'--version']).splitlines()[0])
            records.append('Target: '+run([cc,'-dumpmachine']).strip())
            obj=p/'kernels.o'; binary=p/'host'
            run([cc,'-std=c11','-O2','-c',c,'-o',obj])
            run([cc,'-std=c11','-O2',host,obj,'-lm','-pthread','-ldl','-o',binary])
            run([binary]); checks+=6
            dis=run(['objdump','-d',obj])
            for symbol in names+['hand_'+n for n in ('extract','replace','construct','equal')]:
                match=re.search(rf'^[0-9a-f]+ <{symbol}>:\n(.*?)(?=\n\n|\Z)',dis,re.M|re.S)
                assert match, symbol
                asm=match[0]
                assert not re.search(r'\b(call\w*|push\w*|pop\w*|enter|leave)\b|%[re](sp|bp)\b',asm),(symbol,asm)
                records.append(asm); checks+=1
    if evidence: Path(evidence).write_text('\n'.join(line.rstrip() for line in '\n'.join(records).splitlines())+'\n')
    print(f'packed word residency/ABI: {checks} checks passed')
    return checks

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--evidence')
    check(evidence=parser.parse_args().evidence)
