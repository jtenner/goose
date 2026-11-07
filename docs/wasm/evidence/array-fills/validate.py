import ctypes,fcntl,json,os,pathlib,subprocess,sys,datetime
root=pathlib.Path('/home/dev/Projects/goose-wasm-backend')
out=pathlib.Path('/tmp/goose-wasm-array-fills-20261107')
lock=open('/home/dev/Projects/wago/.performance-measurement.lock','a+')
try:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
except BlockingIOError:
    print('Shared lease is busy; no compiler or test was started.',flush=True)
    sys.exit(75)
ctypes.CDLL(None,use_errno=True).prctl(36,1,0,0,0)
lease={'owner':'Goose array-fill Release validation','pid':os.getpid(),'active':True,'children_reaped':False,'commands':[]}
def save():
    (out/'lease.json').write_text(json.dumps(lease,indent=2)+'\n')
save()
print('Acquired shared lease for build/tests; no performance samples.',flush=True)
commands=[('golden', ['python3', '/tmp/goose-wasm-array-fills-20261107/golden.py']), ('promote', ['python3', '/tmp/goose-wasm-array-fills-20261107/promote.py']), ('build', ['cmake', '--build', 'build', '--parallel', '2']), ('targeted', ['mise', 'exec', 'wasm-tools@1.262.0', 'node@24.22.2', '--', 'python3', '/tmp/goose-wasm-array-fills-20261107/targeted.py']), ('wasm', ['mise', 'exec', 'wasm-tools@1.262.0', 'node@24.22.2', '--', 'python3', 'test/wasm_backend.py', '--exe', 'build/goose', '--wasmtime-python', '/tmp/goose-wasm-runtime-env/bin/python']), ('compatibility', ['python3', 'test/backend_shared.py', '--reference', 'build/goose-inline-checkpoint', '--exe', 'build/goose', '--out', '/tmp/goose-wasm-array-fills-20261107/native-compatibility']), ('equivalence', ['python3', '/tmp/goose-wasm-array-fills-20261107/equivalence.py'])]
exitcode=0
try:
    for name,command in commands:
        print('Start '+name,flush=True)
        with (out/(name+'.stdout')).open('wb') as stdout,(out/(name+'.stderr')).open('wb') as stderr:
            child=subprocess.Popen(command,cwd=root,stdout=stdout,stderr=stderr,start_new_session=True)
            rc=child.wait()
        while True:
            try: os.waitpid(-1,0)
            except ChildProcessError: break
        (out/(name+'.exit')).write_text(str(rc)+'\n')
        lease['commands'].append({'name':name,'command':command,'exit':rc});save()
        print(name+' exit '+str(rc),flush=True)
        if rc:
            exitcode=rc
            break
finally:
    while True:
        try: os.waitpid(-1,0)
        except ChildProcessError: break
    lease['children_reaped']=True
    lease['active']=False
    lease['exit']=exitcode
    save()
    fcntl.flock(lock,fcntl.LOCK_UN)
    lock.close()
    print('All owned children reaped; shared lease released.',flush=True)
sys.exit(exitcode)
