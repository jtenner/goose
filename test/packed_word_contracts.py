#!/usr/bin/env python3
"""Conditional layouts, once-only evaluation, worker values, and atomic CAS."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

SOURCE = '''
packed word Flags:u32 { a:u16, b:u16 }
packed word Counters:u64 { a:u32, b:u32 }
packed word Config:u64 {
 const if build::DEBUG { flag:bool = true } else { _:u1 },
 const if build::DEBUG { const if true { value:u7 = 17 } } else { _:u7 },
 _:u24, high:u32 = 99
}
packed word Empty:u8 { _:u8 }
packed word Inactive:u8 { const if false { bad:u129 = missing() } else { fine:u8 } }
var order:u64=0;
fn next(value:u8)->u8 { order=order*10+value as u64; value }
packed word Defaults:u16 { a:u4=next(1), b:u4=next(2), c:u4=next(3) }
thread_fn add(cap:SharedAtomicU64, right:bool, seed:Counters) {
 assert(seed.a==11); assert(seed.b==12);
 for i in 1000 {
  loop {
   let old=atomic_load(cap,"Acquire");
   var w=old as Counters;
   if right { w.b++; } else { w.a++; }
   let seen,ok=atomic_compare_exchange(cap,old,w as u64,"AcqRel","Acquire");
   if ok { break; }
  }
 }
}
fn main(){
 let c=Config { .. }; print(c as u64); print(c.high);
 let e=Empty {}; print(e as u8);
 let d=Defaults { c:next(6), a:next(4) }; print(order); print(d as u16);
 let o,ok=shared_alloc(16); assert(ok);
 let cap=shared_atomic_u64(o,0,0);
 let a=thread_spawn(add,cap,false,Counters{11,12});
 let b=thread_spawn(add,cap,true,Counters{11,12});
 let c1=thread_spawn(add,cap,false,Counters{11,12});
 let d1=thread_spawn(add,cap,true,Counters{11,12});
 assert(thread_wait(a)); assert(thread_wait(b)); assert(thread_wait(c1)); assert(thread_wait(d1));
 let total=atomic_load(cap,"SeqCst") as Counters; print(total.a); print(total.b);
 let small=shared_atomic_u32(o,8,Flags{5,6} as u32);
 print((atomic_load(small,"Acquire") as Flags).a);
 atomic_store(small,Flags{7,8} as u32,"Release");
 print((atomic_exchange(small,0,"AcqRel") as Flags).b);
 assert(shared_close(o));
}
'''

def check(exe=None):
    exe=exe or os.environ.get('GOOSE_TEST_EXE') or shutil.which('goose++');checks=0
    with tempfile.TemporaryDirectory(prefix='packed-contracts-') as td:
        p=Path(td);s=p/'contract.goose';s.write_text(SOURCE)
        def run(args):
            r=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=120)
            assert r.returncode==0,(args,r.stdout,r.stderr[:5000])
            return r.stdout
        for debug in ('true','false'):
            for level in (0,2):
                c=p/'contract.c';exeout=p/'contract'
                run([exe,f'-O{level}','-D',f'DEBUG={debug}','--standalone','-o',c,s])
                assert 'missing_g' not in c.read_text();checks+=1
                for cc in (os.environ.get('CC','gcc'),os.environ.get('CLANG','clang')):
                    run([cc,f'-O{level}','-fsanitize=undefined','-fno-sanitize-recover=all',c,'-lm','-ldl','-pthread','-o',exeout])
                    actual=run([exeout]).splitlines()
                    expected=[str((99<<32) | (35 if debug=='true' else 0)),'99','0','426',str(4|(2<<4)|(6<<8)),'2000','2000','5','8']
                    assert actual==expected,(debug,level,cc,actual,expected)
                    checks+=len(expected)
    print(f'packed word contracts: {checks} checks passed');return checks

if __name__=='__main__':check()
