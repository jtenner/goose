// Initial growable scalar-array lowering. Storage assignment is complete
// before these methods emit code; data memories are never chosen by type.
#pragma once

namespace goose {

inline TypeExpr *WasmCodeGen::ArrayElement(Node *n) {
    auto t = n->exprtype;
    while (t && t->kind == TY_REF) t = t->ref->sub;
    if (!t || t->kind != TY_ARRAY || !IsResz(t))
        Fail(n->line, "this array layout needs the pending compound lowering");
    Type(t);
    return t->arr->sub;
}

inline uint32_t WasmCodeGen::ArrayHeader(Node *n) {
    ArrayElement(n);
    auto t = n->exprtype;
    while (t->kind == TY_REF) t = t->ref->sub;
    Gen(n); Convert(n->exprtype, t);
    auto header = Local(WasmModule::I32); code.Set(header);
    return header;
}

inline int WasmCodeGen::ArrayMemory(Node *n) {
    if (auto u = Is<Unary>(n); u && u->op == T_BITAND) n = u->child;
    auto id = Is<Ident>(n);
    if (!id || !id->vdef || id->vdef->type->kind != TY_ARRAY || !storage.owners.count(id->vdef)) return -1;
    return storage.Memory(id->vdef, current);
}

inline void WasmCodeGen::InitArray(VarDef *owner, const Slot &slot, Node *init) {
    if (owner->reusable) Fail(owner->line, "pool owners need the pending descriptor lowering");
    while (auto call = Is<Call>(init)) {
        if (!call->defaultinit) break;
        init = call->defaultinit;
    }
    auto literal = Is<ArrayLit>(init);
    if (!literal || literal->fillval || literal->capexpr)
        Fail(init->line, "this array constructor needs the pending destination lowering");
    auto memory = storage.Memory(owner, current);
    auto identity = Local(WasmModule::I32), saved = Local(WasmModule::I32);
    if (memory >= 0) code.I32(memory);
    else StackIndex(storage.owners.at(owner) + 1);
    code.Set(identity);
    if (memory >= 0) { code.Byte(0x23); code.U(memory); }
    else { code.Get(identity); code.Call(memories->Top(false)); }
    code.Set(saved);
    if (!owner->isglobal) {
        assert(!scopes.empty());
        scopes.back().push_back({nullptr, memory >= 0 ? (uint32_t)memory : identity, saved, memory < 0});
    }
    auto header = Local(WasmModule::I32);
    Address(slot); code.Set(header);
    code.Get(header); code.Get(identity); code.Byte(0xad); code.I64(32); code.Byte(0x86);
    code.Get(saved); code.Byte(0xad); code.Byte(0x84); code.Mem(0x37);
    code.Get(header); code.I64(0); code.Mem(0x37, 0, 8);
    for (auto value : literal->elems)
        PushArray(header, owner->type->arr->sub, value, nullptr, value->line, memory);
}

inline void WasmCodeGen::LoadElement(TypeExpr *element, int memory) {
    if (memory >= 0) { code.Byte(0xa7); LoadFixed(element, (uint32_t)memory); }
    else Load(element);
}

inline void WasmCodeGen::StoreElement(TypeExpr *element, int memory) {
    if (memory >= 0) {
        auto value = Temp(element); code.Set(value); code.Byte(0xa7); code.Get(value);
        StoreFixed(element, (uint32_t)memory);
    } else Store(element);
}

inline void WasmCodeGen::PushArray(uint32_t header, TypeExpr *element, Node *value,
                                  TypeExpr *result, Line line, int memory) {
    Gen(value); Convert(value->exprtype, element);
    auto item = Temp(element); code.Set(item);
    // Read the current header after argument effects. A call used for the
    // value can itself append through another reference to this owner.
    auto length = Local(WasmModule::I64), old = Local(WasmModule::I32);
    code.Get(header); code.Mem(0x29, 0, 8); code.Set(length);
    if (memory >= 0) { code.I32((int32_t)Size(element)); code.Call(memories->Reserve(memory)); }
    else {
        code.Get(header); code.Mem(0x29); code.I64(32); code.Byte(0x88); code.Byte(0xa7);
        code.I32((int32_t)Size(element)); code.Call(memories->ReserveDynamic());
    }
    code.Set(old);
    code.Get(header); code.Mem(0x29); code.I64(-4294967296ll); code.Byte(0x83);
    code.Get(old); code.Byte(0xad); code.Byte(0x84);
    auto address = Local(WasmModule::I64); code.Tee(address); code.Get(item); StoreElement(element, memory);
    code.Get(header); code.Get(length); code.I64(1); code.Byte(0x7c); code.Mem(0x37, 0, 8);
    if (!Void(result)) {
        code.Get(address);
        if (result->kind != TY_REF || !TEq(result->ref->sub, element)) {
            LoadElement(element, memory); Convert(element, result);
        }
    }
    (void)line;
}

inline void WasmCodeGen::ElementOffset(uint32_t header, uint32_t index, TypeExpr *element, Line line) {
    auto base = Local(WasmModule::I64), offset = Local(WasmModule::I64);
    code.Get(header); code.Mem(0x29); code.Set(base);
    code.Get(base); code.I64(UINT32_MAX); code.Byte(0x83);
    code.Get(index); code.I64(Size(element)); code.Byte(0x7e); code.Byte(0x7c); code.Tee(offset);
    code.I64(UINT32_MAX); code.Byte(0x56); Open(0x04); Trap(11, line); Close();
    code.Get(base); code.I64(-4294967296ll); code.Byte(0x83); code.Get(offset); code.Byte(0x84);
}

inline pair<TypeExpr *, int> WasmCodeGen::ElementAddress(Index *index) {
    auto element = ArrayElement(index->obj);
    auto header = ArrayHeader(index->obj);
    // C's IndexLoc snapshots the view before an index with statement
    // effects. Snapshot its length here as well; bases remain stable.
    auto length = Local(WasmModule::I64), position = Local(WasmModule::I64);
    code.Get(header); code.Mem(0x29, 0, 8); code.Set(length);
    Gen(index->idx); code.Set(position);
    if (!index->nobc) {
        code.Get(position); code.Get(length); code.Byte(0x5a);
        Open(0x04); Trap(8, index->line); Close();
    }
    ElementOffset(header, position, element, index->line);
    return {element, ArrayMemory(index->obj)};
}

inline void WasmCodeGen::AssignElement(Index *index, Node *rhs, TType op, bool pointee, Line line) {
    auto [type, memory] = ElementAddress(index);
    auto address = Local(WasmModule::I64); code.Set(address);
    if (pointee && type->kind == TY_REF && op != T_DOTASSIGN) {
        code.Get(address); LoadElement(type, memory); CheckNull(line, Type(type));
        if (HeaderRef(type)) Fail(line, "whole-array assignment needs the pending destination lowering");
        code.Set(address); type = type->ref->sub; memory = -1;
    }
    if (op == T_DOTASSIGN) {
        if (type->kind != TY_REF) Fail(line, "reference rebinding requires a reference element");
        if (auto source = Is<Ident>(rhs); source && source->vdef && source->vdef->type->kind != TY_REF) {
            Address(Find(source->vdef)); code.Byte(0xad);
        } else ReferenceValue(rhs, Type(type));
    } else {
        if (op != T_ASSIGN) { code.Get(address); LoadElement(type, memory); }
        if (rhs) { Gen(rhs); Convert(rhs->exprtype, type); }
        else if (type->kind == TY_FLT) {
            if (type->fltstorage == FS_F32) code.F32(1); else code.F64(1);
        } else code.I64(1);
        if (op != T_ASSIGN) Arithmetic(op, type, line);
    }
    auto value = Temp(type); code.Set(value); code.Get(address); code.Get(value); StoreElement(type, memory);
}

inline void WasmCodeGen::ArrayBuiltin(Call *call, const vector<Node *> &arguments) {
    auto element = ArrayElement(arguments[0]);
    auto header = ArrayHeader(arguments[0]);
    auto memory = ArrayMemory(arguments[0]);
    if (call->builtin == B_LEN) { code.Get(header); code.Mem(0x29, 0, 8); return; }
    if (call->builtin == B_PUSH) {
        PushArray(header, element, arguments[1], call->exprtype, call->line, memory); return;
    }
    auto length = Local(WasmModule::I64);
    code.Get(header); code.Mem(0x29, 0, 8); code.Set(length);
    if (call->builtin == B_POP) {
        code.Get(length); code.Byte(0x50); Open(0x04); Trap(9, call->line); Close();
        code.Get(length); code.I64(1); code.Byte(0x7d); code.Set(length);
    } else { code.I64(0); code.Set(length); }
    ElementOffset(header, length, element, call->line);
    auto address = Local(WasmModule::I64); code.Set(address);
    int result = -1;
    if (call->builtin == B_POP) {
        result = (int)Temp(element); code.Get(address); LoadElement(element, memory); code.Set(result);
    }
    if (memory >= 0) { code.Get(address); code.Byte(0xa7); code.Byte(0x24); code.U(memory); }
    else {
        code.Get(header); code.Mem(0x29); code.I64(32); code.Byte(0x88); code.Byte(0xa7);
        code.Get(address); code.Byte(0xa7); code.Call(memories->Top(true));
    }
    code.Get(header); code.Get(length); code.Mem(0x37, 0, 8);
    if (result >= 0) { code.Get(result); Convert(element, call->exprtype); }
}

inline void WasmCodeGen::ArrayFor(ForLoop *loop) {
    auto element = ArrayElement(loop->iter);
    auto id = Is<Ident>(loop->iter);
    auto reload = id && id->vdef && id->vdef->isvar && id->vdef->type->kind == TY_REF;
    auto header = reload ? Local(WasmModule::I32) : ArrayHeader(loop->iter);
    auto memory = ArrayMemory(loop->iter);
    auto position = Local(WasmModule::I64); code.I64(0); code.Set(position);
    auto end = Open(), head = Open(0x03);
    if (reload) {
        auto currentheader = ArrayHeader(loop->iter); code.Get(currentheader); code.Set(header);
    }
    // Growth during iteration is permitted. Read the current count on each
    // test rather than assuming the entry view has a fixed length.
    code.Get(position); code.Get(header); code.Mem(0x29, 0, 8); code.Byte(0x5a); Branch(end, true);
    ElementOffset(header, position, element, loop->line);
    if (!loop->byref || element->kind == TY_REF) {
        LoadElement(element, memory); Convert(element, loop->vdef->type);
    }
    Write(Find(loop->vdef));
    if (loop->idxdef) {
        code.Get(position); Normalize(loop->idxdef->type); Write(Find(loop->idxdef));
    }
    auto step = Open();
    targets.push_back({Target::Loop, nullptr, scopes.size(), end, step, -1, nullptr});
    BlockValue(loop->body, false); targets.pop_back(); Close();
    code.Get(position); code.I64(1); code.Byte(0x7c); code.Set(position);
    Branch(head); Close(); Close();
}

}  // namespace goose
