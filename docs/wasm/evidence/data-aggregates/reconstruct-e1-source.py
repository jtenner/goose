from pathlib import Path
import json,hashlib
b=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend');d=b/'e1-source-reconstruction';d.mkdir(exist_ok=True)
sources=json.loads((b/'build04/source-hashes.json').read_text());rows=[]
for name,want in sources.items():
 s=(r/name).read_text()
 if name=='src/wasm_codegen.h':
  s=s.replace('    uint32_t arraystorevalue = UINT32_MAX;\n','').replace('    array<optional<PushScratch>, 4> fixedpushscratch;\n','').replace('        arraystorevalue = UINT32_MAX; fixedpushscratch.fill(nullopt);\n','')
 if name=='src/wasm_arrays.h':
  s=s.replace('''            if (arraystorevalue == NoLocal) arraystorevalue = Local(WasmModule::I64);
            code.Set(arraystorevalue); code.Byte(0xa7); code.Get(arraystorevalue);''','''            auto value = Local(WasmModule::I64); code.Set(value); code.Byte(0xa7); code.Get(value);''')
 if name=='src/wasm_fixed.h':
  start=s.index('        PushScratch *scratch = nullptr;');end=s.index('\n    }\n}',start)
  s=s[:start]+'''        optional<PushScratch> scratch;
        if (reuse && !literal->elems.empty())
            scratch = PushScratch {Temp(array->arr->sub), Local(WasmModule::I64),
                                   Local(WasmModule::I32), Local(WasmModule::I64),
                                   Local(WasmModule::I64), Local(WasmModule::I64)};
        for (auto value : literal->elems)
            PushArray(place, value, nullptr, value->line, scratch ? &*scratch : nullptr);'''+s[end:]
 data=s.encode();assert hashlib.sha256(data).hexdigest()==want,name
 p=d/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);rows.append({'path':name,'sha256':want})
(d/'provenance.json').write_text(json.dumps({'status':'All reconstructed bytes match original build04 frozen SHA256 manifest.','method':'Reverse only the later unbuilt scratch-cache edits into separate files; production checkout not changed.','compiler_sha256':'e1eacdffc85c2f042b72127579ea332a5426384e373478b571c859f98c87ea42','files':rows},indent=2)+'\n')
print('Verified reconstructed E1 source bytes for',len(rows),'files.')
