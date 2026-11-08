from pathlib import Path
import difflib,hashlib,json
root=Path('/home/dev/Projects/goose-wasm-backend');out=Path(__file__).parent;files={}
def edit(name,changes):
 old=(root/name).read_text();new=old
 for a,b,count in changes:
  assert new.count(a)==count,(name,a,new.count(a),count)
  new=new.replace(a,b)
 files[name]=(old,new)
edit('src/wasm_storage.h',[
 ('    void Walk(Node *n, FnSpec *function, int &next) {','''    bool FixedParameter(TypeExpr *t) {
        return WasmValueSupport::Nominal(t) || (t && t->kind == TY_ARRAY &&
               (t->arr->akind == A_FIXED ||
                (t->arr->akind == A_LIMITED && layout.ArrSize(t->arr) >= 0)));
    }

    void Walk(Node *n, FnSpec *function, int &next) {''',1),
 ('if (WasmValueSupport::Nominal(d->type)) {','if (WasmValueSupport::Nominal(d->type) || (v->inline_arg && FixedParameter(d->type))) {',1),
 ('if (!WasmValueSupport::Nominal(parameter->type)) continue;','if (!FixedParameter(parameter->type)) continue;',1),
 ('if (WasmValueSupport::Nominal(p->type)) {','if (FixedParameter(p->type)) {',1)])
edit('src/wasm_codegen.h',[
 ('    void RequireCallValue(TypeExpr *t, bool result, Line line) {\n        if (Nominal(t)) {','    bool FixedParameter(TypeExpr *t) { return storage.FixedParameter(t); }\n    void RequireCallValue(TypeExpr *t, bool result, Line line) {\n        if (Nominal(t) || (!result && FixedParameter(t))) {',1),
 ('return Nominal(parameter->type);','return FixedParameter(parameter->type);',1),
 ('''                    if (v->inline_arg)
                        Fail(n->line, "by-value arrays need the pending destination lowering");''','''                    if (v->inline_arg) {
                        RequireCallValue(s.type, false, n->line);
                        ConstructFixed(FreshOwner(v->defs[i], v), v->inits[i]); continue;
                    }''',1),
 ('                if (Nominal(s.type)) {','                if (FixedParameter(s.type)) {',2),
 ('args.push_back(Nominal(p->type) ? WasmModule::I32 : Type(p->type));','args.push_back(FixedParameter(p->type) ? WasmModule::I32 : Type(p->type));',1)])
# The generic declaration branch must keep nominal scope. Arrays were already
# handled immediately above it; using FixedParameter there is harmless but
# retain the narrow existing spelling to avoid an unrelated branch change.
old,new=files['src/wasm_codegen.h'];new=new.replace('''                if (FixedParameter(s.type)) {
                    if (v->inline_arg)''','''                if (Nominal(s.type)) {
                    if (v->inline_arg)''');files['src/wasm_codegen.h']=(old,new)
edit('src/wasm_fixed.h',[
 ('    if (Nominal(owner->type)) {','    if (Nominal(owner->type) || storage.fixedvalues.count(owner)) {',1),
 ('if (!Nominal(owner->type) || !image ||','if (!FixedParameter(owner->type) || !image ||',1),
 ('    if (Nominal(type)) {\n        WithFixedTemporary','    if (FixedParameter(type)) {\n        WithFixedTemporary',1),
 ('if (Nominal(parameter->type)) ConstructFixed','if (FixedParameter(parameter->type)) ConstructFixed',1)])
text=''.join(''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='a/'+name,tofile='b/'+name)) for name,(a,b) in files.items());(out/'implementation.patch').write_text(text)
(out/'patch-parent-hashes.json').write_text(json.dumps({name:hashlib.sha256(a.encode()).hexdigest() for name,(a,b) in files.items()},indent=2)+'\n')
print('prepared',len(files),'files; no production edits')
