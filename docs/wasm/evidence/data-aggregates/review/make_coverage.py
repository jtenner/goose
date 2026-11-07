from pathlib import Path
import json,collections
P=Path('/tmp/goose-wasm-data-aggregates-review-20261107');R=Path('/tmp/goose-wasm-data-aggregates-20261107');O=P/'review';S=P/'snapshot';W=Path('/home/dev/Projects/goose-wasm-backend');A=S/'docs/wasm/evidence/data-aggregates'
scope=json.loads((P/'scope.json').read_text());audit=json.loads((O/'archive-and-provenance.json').read_text());reads=[json.loads(x) for x in (O/'read-log.jsonl').read_text().splitlines()]
semantic=collections.defaultdict(set);modes=collections.defaultdict(set)
for e in reads:semantic[e['path']].update(range(e['first'],e['last']+1));modes[e['path']].add('semantic text, line ranges recorded')
for name in ['artifact-read-log.json','remaining-read-log.json']:
 for e in json.loads((O/name).read_text()):modes[e['path']].add(e['mode'])
# Carry coverage across verified byte-identical archive/raw pairs only.
for e in audit['archive']:
 a=str(A/e['archived']);b=e['source'];u=semantic[a]|semantic[b];semantic[a]=set(u);semantic[b]=set(u);u=modes[a]|modes[b]|{'raw/archive/index/snapshot hash verified'};modes[a]=set(u);modes[b]=set(u)
for rel in audit['exit_values']:
 for f in [A/rel,R/rel]:modes[str(f)].add('parsed exact exit status, not workload replay')
for rel in audit['nonempty_stderr']:
 for f in [A/rel,R/rel]:modes[str(f)].add('full stderr extracted to archive-and-provenance.json; semantic review only where line ranges recorded')
for unit in ['build05','build04']:
 modes[str(R/unit/'source-hashes.json')].add('all source manifest entries independently hash checked')
for unit in ['full-wasm04','compatibility02']:
 modes[str(R/unit/'validation-input-hashes.json')].add('all 4222 entries checked against current bytes; exact comment changes identified')
for f in (R/'e1-source-reconstruction/src').rglob('*'):
 if f.is_file():modes[str(f)].add('checked against original build04 source hash manifest; no semantic reading implied')
for e in scope['main_changed_files']:
 f=S/e;w=W/e
 semantic[str(f)]|=semantic[str(w)];modes[str(f)]|=modes[str(w)];modes[str(f)].add('snapshot/worktree/index expected hashes verified')
for e in scope['context']:
 f=P/'context'/e;w=W/e
 semantic[str(f)]|=semantic[str(w)];modes[str(f)]|=modes[str(w)];modes[str(f)].add('context/worktree/index expected hashes verified')
def ranges(vals):
 out=[]
 for x in sorted(vals):
  if out and x==out[-1][1]+1:out[-1][1]=x
  else:out.append([x,x])
 return out
def entry(f,group,byte_size=None):
 f=Path(f);key=str(f);size=f.stat().st_size if byte_size is None else byte_size;seen=semantic[key];ms=sorted(modes[key]);total=None;missing=None
 if seen:
  total=len(f.read_bytes().splitlines());missing=ranges(set(range(1,total+1))-seen)
 status='semantic full text' if seen and not missing else 'semantic partial text' if seen else 'empty file' if size==0 else 'parsed or byte-compared' if any(not ('hash' in x or 'extracted' in x) for x in ms) else 'hash or inventory only'
 if status=='semantic full text':reason='Full text reviewed; this does not imply execution or binary instruction review.'
 elif status=='semantic partial text':reason='Relevant ranges reviewed; remaining ranges are outside the constructor, layout, lifecycle, or harness questions reviewed.'
 elif status=='empty file':reason='No semantic content.'
 elif f.suffix in ['.wasm','.bin']:reason='No full instruction-level or byte-by-byte semantic review. Selected section/local metrics and memory models were checked where modes state this; other generated modules are outside the selected comparisons.'
 elif f.name=='goose-tested' or f.suffix=='.native' or f.suffix=='.o':reason='Executable/object was not run or disassembled. Provenance hashes were checked where recorded.'
 elif f.suffix=='.exit':reason='Exit value parsed where recorded. Exit status alone is not proof of behavior.'
 elif f.suffix=='.json':reason='Manifest/result data checked only as described by modes. Hashes and metadata do not substitute for source or behavior review.'
 elif f.suffix in ['.c','.wat']:reason='Generated representation not fully reviewed. Selected byte comparisons or mutation checks are listed in modes; source and relevant harnesses were reviewed instead.'
 elif 'e1-source-reconstruction' in str(f):reason='Retrospective reconstructed source hash checked; full earlier compiler source is outside semantic review of the current increment.'
 elif 'artifacts' in f.parts:reason='Broad-suite intermediate artifact not semantically inspected; current source, harness, suite completion, and selected shared-path artifacts were inspected.'
 elif f.suffix in ['.stdout','.stderr']:reason='Redundant command stream not fully read unless semantic ranges are listed. Selected diagnostics, expected-output checks, or byte comparisons are listed in modes.'
 else:reason='Not needed for selected claims beyond stated inventory/hash/parsed checks; no semantic inspection claimed.'
 return {'path':key,'group':group,'bytes':size,'status':status,'semantic_line_ranges':ranges(seen),'unread_line_ranges':missing,'total_lines_if_read':total,'checks':ms,'limit_or_reason':reason}
main=[entry(S/x,'main changed') for x in scope['main_changed_files']];assert all(e['status']=='semantic full text' for e in main),[e for e in main if e['status']!='semantic full text']
context=[entry(P/'context'/x,'context') for x in scope['context']]
archive=[entry(S/x,'archived evidence') for x in scope['archived_evidence_files']]
raw=[entry(e['path'],'raw evidence',e['bytes']) for e in json.loads((P/'raw-inventory.json').read_text())]
allrows=main+context+archive+raw
extra=sorted(set(modes)|set(semantic)-{e['path'] for e in allrows})
# Report only additional inspected paths, not review output files.
extra=[entry(f,'additional inspected input') for f in extra if Path(f).is_file() and not str(f).startswith(str(O)) and f not in {e['path'] for e in allrows} and (modes[f] or semantic[f])]
allrows+=extra
summary={g:dict(collections.Counter(e['status'] for e in allrows if e['group']==g)) for g in dict.fromkeys(e['group'] for e in allrows)}
(O/'coverage.json').write_text(json.dumps({'method':'Line logs record text inspected. Parser and hash checks are separate. Verified identical archive/raw files share text coverage. No workload was replayed. Main-file output gaps were reread during review.','summary':summary,'files':allrows},indent=2)+'\n')
with (O/'unread-evidence.tsv').open('w') as out:
 out.write('path\tstatus\tunread_line_ranges\treason\tchecks\n')
 for e in archive+raw:
  if e['status']!='semantic full text':out.write('\t'.join([e['path'],e['status'],json.dumps(e['unread_line_ranges']),e['limit_or_reason'],'; '.join(e['checks'])])+'\n')
(O/'coverage-summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2));print('explicit evidence paths',len(archive)+len(raw))
