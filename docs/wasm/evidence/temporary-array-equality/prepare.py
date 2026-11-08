from pathlib import Path
import difflib,hashlib,json
root=Path('/home/dev/Projects/goose-wasm-backend');raw=Path(__file__).parent
file='src/wasm_arrays.h';old=(root/file).read_text();a=old.index('inline void WasmCodeGen::ArrayEquality(');z=old.index('\ninline bool WasmCodeGen::ArrayPathHasStatements',a);body=old[a:z]
start=body.index('    auto result = Local(WasmModule::I32)');end=body.rfind('\n}')
loop=body[start:end].replace('left.elementMemory','leftview.place.elementMemory').replace('right.layout.element','rightview.place.layout.element').replace('right.elementMemory','rightview.place.elementMemory')
new='''inline void WasmCodeGen::ArrayEquality(Binary *node) {
    auto scoped = HasFixedTemporary(node->left) || HasFixedTemporary(node->right) ||
                  ArrayPathHasStatements(node->right);
    auto lefttype = ArrayType(node->left), righttype = ArrayType(node->right);
    if (Nominal(lefttype->arr->sub) || Nominal(righttype->arr->sub))
        Fail(node->line, "aggregate array equality needs the pending value lowering");
    auto element = lefttype->arr->sub;
    auto compare = [&](const ArrayView &leftview, const ArrayView &rightview, uint32_t length) {
'''+''.join('    '+line+'\n' for line in loop.splitlines())+'''    };
    if (scoped) {
        if (!InlineArray(lefttype))
            Fail(node->line, "effectful array comparison needs the pending destination lowering");
        auto result = Local(WasmModule::I32);
        // Native value equality captures the left image before evaluating the right.
        WithFixedTemporary(lefttype, node->left, [&](const FixedPlace &image) {
            auto left = ArrayFromPlace(image, node->line);
            auto length = Local(WasmModule::I64);
            auto leftprefix = VarintPrefix(lefttype) ? Local(WasmModule::I32) : NoLocal;
            auto rightprefix = VarintPrefix(righttype) ? Local(WasmModule::I32) : NoLocal;
            auto leftview = CaptureArrayView(left, length, leftprefix);
            auto finish = [&](const ArrayPlace &right) {
                compare(leftview, {right, NoLocal, rightprefix}, length);
                code.Set(result);
            };
            if (HasFixedTemporary(node->right)) {
                WithReadPlace(node->right, [&](FixedPlace selected) {
                    while (selected.type->kind == TY_REF) selected = DereferencePlace(selected, node->line);
                    finish(ArrayFromPlace(selected, node->line));
                });
            } else finish(ResolveArray(node->right));
        });
        code.Get(result);
        return;
    }
    auto left = ResolveArray(node->left); auto length = Local(WasmModule::I64);
    auto leftprefix = VarintPrefix(lefttype) ? Local(WasmModule::I32) : NoLocal;
    auto rightprefix = VarintPrefix(righttype) ? Local(WasmModule::I32) : NoLocal;
    auto leftview = CaptureArrayView(left, length, leftprefix);
    auto right = ResolveArray(node->right); ArrayView rightview {right, NoLocal, rightprefix};
    compare(leftview, rightview, length);
}
'''
result=old[:a]+new+old[z:]
(raw/'implementation.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),result.splitlines(True),fromfile='a/'+file,tofile='b/'+file)))
(raw/'patch-parent-hashes.json').write_text(json.dumps({file:hashlib.sha256(old.encode()).hexdigest()},indent=2)+'\n')
print('Prepared patch only; no source edit')
