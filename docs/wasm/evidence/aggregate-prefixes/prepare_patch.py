from pathlib import Path
import json,hashlib
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend')
s=(r/'src/wasm_support.h').read_text();old='layout.LenStore(t->arr) == IS_U32 && Nominal(t->arr->sub)';assert s.count(old)==1;s=s.replace(old,'layout.LenStore(t->arr) != IS_VARINT && Nominal(t->arr->sub)');(p/'proposed-wasm_support.h').write_text(s)
s=(r/'src/wasm_arrays.h').read_text();old='''    if (!stride || prefix != 4) Fail(owner->line, "aggregate data construction needs a positive fixed u32 layout");''';new='''    if (!stride || (prefix != 1 && prefix != 2 && prefix != 4 && prefix != 8))
        Fail(owner->line, "aggregate data construction needs a positive fixed unsigned prefix layout");''';assert s.count(old)==1;s=s.replace(old,new)
old='''    if (literalCount != NoLocal) {
        if (count != NoLocal || literalCount > (UINT32_MAX - prefix) / stride)''';new='''    if (literalCount != NoLocal) {
        if (prefix < 8 && literalCount > ((1ull << (prefix * 8)) - 1))
            Fail(owner->line, "array length exceeds its stored prefix");
        if (count != NoLocal || literalCount > (UINT32_MAX - prefix) / stride)''';assert s.count(old)==1;s=s.replace(old,new)
(p/'proposed-wasm_arrays.h').write_text(s)
(p/'patch-inputs.json').write_text(json.dumps({n:hashlib.sha256((r/n).read_bytes()).hexdigest() for n in ['src/wasm_arrays.h','src/wasm_support.h']},indent=2)+'\n')
(p/'source-search.md').write_text('''# Read-only source bug search\n\nNative GPT-6.1-Sol high worker inspected fixed-prefix aggregate paths. It made\nno edits and ran no build, guest, timing or lease command. No additional\nfour-byte offset was found in fresh children, nested arrays, copies, reference\naccess or ArrayFor. Source offsets remain layout-based. Aggregate equality is\nstill gated. Parser admits u8/u16/u32/u64/varint length storage only.\n\nThe worker identified an existing compile-time rejection for a known oversized\nfixed source in InitFixedArrayValue, separate from ReserveFreshDataArray.\nThis is a limit, not a confirmed production defect. Scalar literal construction\nhas the same compile-time prefix-range policy. The proposed aggregate literal\npath retains that policy. Exact-copy count width is already proved by the source
layout equality and unsigned count load; the existing byte-size check remains.\n\nWide-count-elements expectations in struct/enum admission tests need updates.\nRequired tests include fixed/limited child arrays, copied binders, references,\nexact copies and complete memory images. Worker test sketches are not runtime\nevidence. Native parent results are saved separately.\n''')
print('two proposed source files,repository unchanged')
