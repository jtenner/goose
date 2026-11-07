import pathlib,json,sys
P=pathlib.Path('/tmp/goose-wasm-data-aggregates-review-20261107'); log=P/'review/read-log.jsonl'
for spec in sys.argv[1:]:
 a=spec.rsplit(':',1); span=None
 if len(a)==2 and a[1].replace('-','').isdigit():spec=a[0];span=a[1]
 f=pathlib.Path(spec);f=f if f.is_absolute() else P/spec
 lines=f.read_text(errors='replace').splitlines();lo,hi=(map(int,span.split('-')) if span else (1,len(lines)))
 print('\nFILE',f,'LINES',lo,hi,'TOTAL',len(lines))
 for n in range(lo,min(hi,len(lines))+1):print(f'{n}: {lines[n-1]}')
 with log.open('a') as out:out.write(json.dumps({'path':str(f),'first':lo,'last':min(hi,len(lines)),'total':len(lines),'mode':'semantic text'})+'\n')
