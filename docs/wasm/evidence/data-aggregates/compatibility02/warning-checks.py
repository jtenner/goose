from pathlib import Path
import hashlib,json,re,subprocess,sys
r=Path('/home/dev/Projects/goose-wasm-backend');p=Path(__file__).parent;b=p.parent
sys.path.insert(0,str(r/'test'))
from run_tests import warning_markers,unmatched_warnings
rows=[]
for e in json.loads((p/'warning-marker-provenance.json').read_text()):
 source=r/e['source'];before=(b/'native-baseline01/failed-warning-fixtures'/source.name).read_bytes();prefix=''.join('// warning: '+m+'\n' for m in e['added_comment_lines']).encode()
 assert source.read_bytes()==prefix+before
 assert hashlib.sha256(before).hexdigest()==e['before']
 for opt in [0,2]:
  command=[str(b/'build05/goose-tested'),'--stats','--roundtrip','--check',f'-O{opt}',str(source)]
  result=subprocess.run(command,cwd=r,capture_output=True)
  stem=source.stem+f'-O{opt}';(p/(stem+'.stdout')).write_bytes(result.stdout);(p/(stem+'.stderr')).write_bytes(result.stderr);(p/(stem+'.exit')).write_text(str(result.returncode)+'\n')
  assert result.returncode==0,(stem,result.returncode)
  out=result.stdout.decode();err=result.stderr.decode();warnings=[(m[0],m[1]) for m in (re.match(r'\S.*?: warning: (.*)$',line) for line in out.splitlines()+err.splitlines()) if m]
  missing,extra=unmatched_warnings(warning_markers(source),warnings)
  assert not missing and not extra,(stem,missing,extra)
  assert 'roundtrip ok:' in out+err and 'typechecked ok:' in out+err,stem
  rows.append({'source':e['source'],'opt':opt,'exit':result.returncode,'warnings':len(warnings),'markers_match':True,'parse_roundtrip_typecheck':True})
(p/'warning-check-results.json').write_text(json.dumps(rows,indent=2)+'\n');print('PASS: 4 parse/roundtrip/typecheck warning checks; comments only; prior native execution groups retained.')
