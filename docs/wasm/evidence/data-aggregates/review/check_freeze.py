import hashlib,json,pathlib,subprocess,sys,os
P=pathlib.Path('/tmp/goose-wasm-data-aggregates-review-20261107'); S=json.loads((P/'scope.json').read_text()); W=pathlib.Path(S['production_worktree'])
def sha(b): return hashlib.sha256(b).hexdigest()
def git(*args):
 r=subprocess.run(['git','--no-optional-locks','-C',str(W),*args],capture_output=True); return r
out={'phase':sys.argv[1],'files':{},'context':{},'baseline':{},'errors':[]}
for f,h in json.loads((P/'changed-file-hashes.json').read_text()).items():
 idx=git('show',':'+f); d={'expected':h,'snapshot':sha((P/'snapshot'/f).read_bytes()),'worktree':sha((W/f).read_bytes()),'index':sha(idx.stdout),'index_exit':idx.returncode}; out['files'][f]=d
 if idx.returncode or any(d[k]!=h for k in ['snapshot','worktree','index']):out['errors'].append(f)
for f,h in json.loads((P/'context-file-hashes.json').read_text()).items():
 d={'expected':h,'packet':sha((P/'context'/f).read_bytes()),'worktree':sha((W/f).read_bytes()),'index':sha(git('show',':'+f).stdout)};out['context'][f]=d
 if any(d[k]!=h for k in ['packet','worktree','index']):out['errors'].append(f)
for f in S['main_changed_files']:
 q=P/'baseline'/f
 if q.exists():
  d={'packet':sha(q.read_bytes()),'git_baseline':sha(git('show',S['baseline']+':'+f).stdout)};out['baseline'][f]=d
  if d['packet']!=d['git_baseline']:out['errors'].append('baseline:'+f)
for k,args in [('head',['rev-parse','HEAD']),('branch',['branch','--show-current']),('unstaged',['diff','--name-only']),('staged_names',['diff','--cached','--name-only']),('diff_check',['diff','--cached','--check'])]:
 r=git(*args);out[k]={'exit':r.returncode,'stdout':r.stdout.decode(),'stderr':r.stderr.decode()}
r=git('diff','--cached','--binary');out['patch']={'packet':sha((P/'staged.patch').read_bytes()),'index':sha(r.stdout),'expected':S['patch_sha256']}
exe=[pathlib.Path(S['raw_root'])/'build05/goose-tested',pathlib.Path(S['raw_root'])/'build04/goose-tested',pathlib.Path('/tmp/goose-wasm-inline-ref-abi-20261107/build04/goose-tested')]
out['executables']={str(f):sha(f.read_bytes()) for f in exe}
(P/'review'/('hashes-'+sys.argv[1]+'.json')).write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k not in ['files','context','baseline','staged_names']},indent=2));print('verified counts',len(out['files']),len(out['context']),len(out['baseline']))
