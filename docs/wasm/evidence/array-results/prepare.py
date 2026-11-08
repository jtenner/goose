from pathlib import Path
import difflib,hashlib,json
root=Path('/home/dev/Projects/goose-wasm-backend');out=Path(__file__).parent;files={}
def edit(name,changes):
 old=(root/name).read_text();new=old
 for a,b,count in changes:
  assert new.count(a)==count,(name,a,new.count(a),count)
  new=new.replace(a,b)
 files[name]=(old,new)
edit('src/wasm_codegen.h',[
 ('bool FixedParameter(TypeExpr *t) { return storage.FixedParameter(t); }','bool FixedParameter(TypeExpr *t) { return storage.FixedParameter(t); }\n    bool FixedResult(TypeExpr *t) { return FixedParameter(t); }',1),
 ('if (Nominal(t) || (!result && FixedParameter(t))) {','if (FixedParameter(t)) {',1),
 ('if (Nominal(ActualType(c)))','if (FixedResult(ActualType(c)))',1),
 ('if (Nominal(ret)) Fail(n->line, "aggregate inline results need a checked destination");','if (FixedResult(ret)) Fail(n->line, "aggregate inline results need a checked destination");',1),
 ('if (Nominal(actual) && (!call || call->builtin < 0)) {','if (FixedResult(actual) && (!call || call->builtin < 0)) {',1),
 ('auto fixed = Nominal(ret);','auto fixed = FixedResult(ret);',1),
 ('if (!Nominal(r)) rets.push_back(Type(r));','if (!FixedResult(r)) rets.push_back(Type(r));',1),
 ('if (!sp->rets.empty() && Nominal(sp->rets[0])) args.push_back(WasmModule::I32);','if (!sp->rets.empty() && FixedResult(sp->rets[0])) args.push_back(WasmModule::I32);',1)])
edit('src/wasm_fixed.h',[
 ('!current || current->rets.size() != 1 || !Nominal(current->rets[0])','!current || current->rets.size() != 1 || !FixedResult(current->rets[0])',1),
 ('!function || function->rets.size() != 1 || !Nominal(function->rets[0])','!function || function->rets.size() != 1 || !FixedResult(function->rets[0])',1),
 ('if (!Nominal(type) || !TEq(type, destination.place.type))','if (!FixedResult(type) || !TEq(type, destination.place.type))',1),
 ('(!array && (Is<Block>(source) || Is<IfExpr>(source)))','(Is<Block>(source) || Is<IfExpr>(source))',1),
 ('&& Nominal(ActualType(source)))','&& FixedResult(ActualType(source)))',2),
 ('if (Nominal(type)) {\n        if (auto block = Is<Block>(source))','if (FixedResult(type)) {\n        if (auto block = Is<Block>(source))',1)])
edit('src/wasm_arrays.h',[
 ('''    if (owner->reusable) Fail(owner->line, "pool owners need the pending descriptor lowering");
    if (auto call = Is<Call>(init);''','''    if (owner->reusable) Fail(owner->line, "pool owners need the pending descriptor lowering");
    auto resultCall = Is<Call>(init);
    if (InlineArray(owner->type) &&
        ((((resultCall && resultCall->builtin < 0) || Is<InlineBlock>(init)) && FixedResult(ActualType(init))) ||
         Is<Block>(init) || Is<IfExpr>(init))) {
        ConstructFixed(FreshOwner(owner, declaration), init); return;
    }
    if (auto call = Is<Call>(init);''',1)])
text=''.join(''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='a/'+name,tofile='b/'+name)) for name,(a,b) in files.items());(out/'implementation.patch').write_text(text)
(out/'patch-parent-hashes.json').write_text(json.dumps({name:hashlib.sha256(a.encode()).hexdigest() for name,(a,b) in files.items()},indent=2)+'\n')
print('prepared',len(files),'files; no production edits')
