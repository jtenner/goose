from pathlib import Path
import hashlib,json
r=Path('/home/dev/Projects/goose-wasm-backend');p=Path(__file__).parent
s=(r/'src/wasm_arrays.h').read_text();original=s
s=s.replace('InitLimitedArrayValue','InitCountedArrayValue')
a=s.index('inline bool WasmCodeGen::InitCountedArrayValue');b=s.index('\ninline void WasmCodeGen::InitArrayCopy',a)
body=s[a:b]
old='''    if (!from || !InlineArray(from) || from->arr->akind != A_LIMITED) return false;'''
new='''    auto variable = from && VariableArray(from) && !TEq(array, from);
    if (!variable && (!from || !InlineArray(from) || from->arr->akind != A_LIMITED)) return false;'''
assert body.count(old)==1;body=body.replace(old,new)
body=body.replace('    RequireFixed(from, source->line);','    if (!variable) RequireFixed(from, source->line);')
old='''        ArrayLength(ArrayFromPlace(value, source->line)); code.Set(count);'''
new='''        if (variable) {
            auto place = ArrayFromPlace(value, source->line);
            auto sourcePrefix = VarintPrefix(from) ? Local(WasmModule::I32) : NoLocal;
            auto view = CaptureArrayView(place, count, sourcePrefix);
            auto zero = Local(WasmModule::I64), payload = Local(WasmModule::I64);
            code.I64(0); code.Set(zero);
            ElementOffset(view, zero, source->line); code.Set(payload);
            value = {from->arr->sub, payload, 0, place.elementMemory, true, true};
        } else { ArrayLength(ArrayFromPlace(value, source->line)); code.Set(count); }'''
assert body.count(old)==1;body=body.replace(old,new)
body=body.replace('width < 8 && (uint64_t)ArrSize(from->arr) > ((1ull << (width * 8)) - 1)', 'width < 8 && (variable || (uint64_t)ArrSize(from->arr) > ((1ull << (width * 8)) - 1))')
old='''        // The fixed source span proves that count * stride fits memory32.
        code.Get(count); code.I64(stride); code.Byte(0x7e); code.Byte(0xa7); code.Set(payload);'''
new='''        // Fixed sources already prove the product; stored variable counts need a check.
        if (variable) {
            code.Get(count); code.I64(UINT32_MAX / stride); code.Byte(0x56);
            Open(0x04); Trap(6, source->line); Close();
        }
        code.Get(count); code.I64(stride); code.Byte(0x7e); code.Byte(0xa7); code.Set(payload);'''
assert body.count(old)==1;body=body.replace(old,new)
old='''        auto sourcePrefix = (uint32_t)IntSize(LenStore(from->arr));
        if (sourcePrefix > UINT32_MAX - value.offset)
            Fail(source->line, "limited array source offset exceeds memory32");
        value.offset += sourcePrefix; value.type = from->arr->sub;'''
new='''        if (!variable) {
            auto sourcePrefix = (uint32_t)IntSize(LenStore(from->arr));
            if (sourcePrefix > UINT32_MAX - value.offset)
                Fail(source->line, "limited array source offset exceeds memory32");
            value.offset += sourcePrefix; value.type = from->arr->sub;
        }'''
assert body.count(old)==1;body=body.replace(old,new)
s=s[:a]+body+s[b:]
(p/'proposed-wasm_arrays.h').write_text(s)
c=(r/'src/wasm_codegen.h').read_text();(p/'proposed-wasm_codegen.h').write_text(c.replace('InitLimitedArrayValue','InitCountedArrayValue'))
(p/'patch-inputs.json').write_text(json.dumps({n:hashlib.sha256((r/n).read_bytes()).hexdigest() for n in ['src/wasm_arrays.h','src/wasm_codegen.h']},indent=2)+'\n')
print('proposed files only; repository unchanged')
