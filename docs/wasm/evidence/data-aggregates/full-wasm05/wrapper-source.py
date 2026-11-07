from pathlib import Path
import ctypes,fcntl,json,os,subprocess,sys,datetime,hashlib
root=Path('/home/dev/Projects/goose-wasm-backend');out=Path(sys.argv[1]).resolve()
assert out.parent==Path(__file__).parent.resolve()
commands=json.loads((out/'commands.json').read_text());assert len({x[0] for x in commands})==len(commands)
assert not (out/'lease.json').exists() and not (out/'unit.stdout').exists(), 'Refuse to overwrite an earlier unit.'
lock=open('/home/dev/Projects/wago/.performance-measurement.lock','a+')
try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
except BlockingIOError:print('Shared lease busy; no child started.');sys.exit(75)
ctypes.CDLL(None,use_errno=True).prctl(36,1,0,0,0)
with (out/'unit.stdout').open('x') as stdout,(out/'unit.stderr').open('x') as stderr:
 os.dup2(stdout.fileno(),1);os.dup2(stderr.fileno(),2)
 wrapper_source=Path(__file__).read_bytes()
 (out/'wrapper-source.py').write_bytes(wrapper_source)
 lease={'owner':'Goose aggregate data-array functional unit','pid':os.getpid(),'active':True,'acquired':True,'wrapper_sha256':hashlib.sha256(wrapper_source).hexdigest(),'children_reaped':False,'commands':[]}
 with (out/'lease.json').open('x') as initial:json.dump(lease,initial,indent=2)
 def save():(out/'lease.json').write_text(json.dumps(lease,indent=2)+'\n')
 def reap():
  while True:
   try:os.waitpid(-1,0)
   except ChildProcessError:break
 rc=1
 try:
  for name,command in commands:
   print('Start '+name,flush=True)
   with (out/(name+'.stdout')).open('xb') as childout,(out/(name+'.stderr')).open('xb') as childerr:
    child=subprocess.Popen(command,cwd=root,stdout=childout,stderr=childerr,start_new_session=True);rc=child.wait()
   reap();(out/(name+'.exit')).write_text(str(rc)+'\n');lease['commands'].append({'name':name,'command':command,'exit':rc});save();print(name+' exit '+str(rc),flush=True)
   if rc:break
 except BaseException:
  rc=1
  raise
 finally:
  reap();lease.update(active=False,children_reaped=True,exit=rc,released_at=datetime.datetime.now(datetime.timezone.utc).isoformat());save();fcntl.flock(lock,fcntl.LOCK_UN);lock.close();(out/'unit.exit').write_text(str(rc)+'\n');print('All children reaped; lease released.',flush=True)
sys.exit(rc)
