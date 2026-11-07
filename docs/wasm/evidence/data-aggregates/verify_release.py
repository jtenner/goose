from pathlib import Path
import os,json,fcntl,datetime,sys,hashlib
p=Path(sys.argv[1]);lease=json.loads((p/'lease.json').read_text());assert not Path('/proc/'+str(lease['pid'])).exists();assert lease['children_reaped'] and not lease['active']
assert lease['acquired'] is True
assert hashlib.sha256((p/'wrapper-source.py').read_bytes()).hexdigest()==lease['wrapper_sha256']
anc={os.getpid()};par=os.getppid()
while par and par not in anc:
 anc.add(par)
 try:par=int(Path(f'/proc/{par}/stat').read_text().split(') ')[1].split()[1])
 except FileNotFoundError:break
matches=[]
for d in Path('/proc').iterdir():
 if not d.name.isdigit() or int(d.name) in anc:continue
 try:a=(d/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')
 except (FileNotFoundError,PermissionError,ProcessLookupError):continue
 if str(p)+'/' in a:matches.append({'pid':int(d.name),'args':a})
assert not matches,matches
with open('/home/dev/Projects/wago/.performance-measurement.lock','a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(lock,fcntl.LOCK_UN)
v={'owner_pid':lease['pid'],'owner_exited':True,'children_reaped':True,'lease_active':False,'lease_acquired':True,'wrapper_snapshot_matches':True,'exact_owned_processes':matches,'nonblocking_exclusive_probe':'PASS','probe_released':True,'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit':lease['exit']}
(p/'release-verification.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v))
