// Initial growable scalar-array lowering. Storage assignment is complete
// before these methods emit code; data memories are never chosen by type.
#pragma once

namespace goose {

inline TypeExpr *WasmCodeGen::ArrayType(Node *n) {
    auto t = n->exprtype;
    while (t && t->kind == TY_REF) t = t->ref->sub;
    if (!t || t->kind != TY_ARRAY || (!IsResz(t) && !InlineArray(t) && !VariableArray(t)))
        Fail(n->line, "this array layout needs the pending compound lowering");
    Type(t);
    return t;
}

inline TypeExpr *WasmCodeGen::ArrayElement(Node *n) { return ArrayType(n)->arr->sub; }

inline void WasmCodeGen::ArrayLength(uint32_t header, TypeExpr *array, int memory) {
    if (array->arr->akind == A_FIXED) { code.I64(ArrSize(array->arr)); return; }
    code.Get(header);
    if (IsResz(array)) { code.Mem(0x29, 0, 8); return; }
    auto bytes = IntSize(LenStore(array->arr));
    auto opcode = (uint8_t)(bytes == 1 ? 0x31 : bytes == 2 ? 0x33 : bytes == 4 ? 0x35 : 0x29);
    if (!VariableArray(array)) code.Mem(opcode);
    else if (memory >= 0) { code.Byte(0xa7); code.Mem(opcode, (uint32_t)memory); }
    else code.Call(memories->Access(opcode));
}

inline void WasmCodeGen::StoreArrayLength(TypeExpr *array, int memory) {
    if (IsResz(array)) { code.Mem(0x37, 0, 8); return; }
    auto bytes = IntSize(LenStore(array->arr));
    auto opcode = (uint8_t)(bytes == 1 ? 0x3c : bytes == 2 ? 0x3d : bytes == 4 ? 0x3e : 0x37);
    if (!VariableArray(array)) code.Mem(opcode);
    else if (memory >= 0) {
        auto value = Local(WasmModule::I64); code.Set(value); code.Byte(0xa7); code.Get(value);
        code.Mem(opcode, (uint32_t)memory);
    } else code.Call(memories->Access(opcode));
}

inline uint32_t WasmCodeGen::ArrayHeader(Node *n) {
    ArrayElement(n);
    auto t = n->exprtype;
    while (t->kind == TY_REF) t = t->ref->sub;
    Gen(n); Convert(n->exprtype, t);
    auto header = Local(Type(t)); code.Set(header);
    return header;
}

inline int WasmCodeGen::ArrayMemory(Node *n) {
    if (InlineArray(ArrayType(n))) return 0;
    if (auto u = Is<Unary>(n); u && u->op == T_BITAND) n = u->child;
    auto id = Is<Ident>(n);
    if (!id || !id->vdef || id->vdef->type->kind != TY_ARRAY || !storage.owners.count(id->vdef)) return -1;
    return storage.Memory(id->vdef, current);
}

inline void WasmCodeGen::InitByteString(VarDef *owner, const Slot &slot, StrLit *literal) {
    auto array = owner->type;
    if (!ByteArray(array)) Fail(literal->line, "string literals require byte elements");
    auto count = literal->val.size();
    auto prefix = VariableArray(array) ? (uint32_t)IntSize(LenStore(array->arr)) : 0u;
    if (count > UINT32_MAX - prefix) Fail(owner->line, "array allocation exceeds memory32");
    if (prefix && prefix < 8 && count > ((1ull << (prefix * 8)) - 1))
        Fail(owner->line, "array length exceeds its stored prefix");
    auto memory = InlineArray(array) ? 0 : storage.Memory(owner, current);
    auto base = Local(WasmModule::I64);
    if (InlineArray(array)) {
        auto header = Local(WasmModule::I32); Address(slot); code.Set(header);
        if (array->arr->akind == A_LIMITED) {
            code.Get(header); code.I64((int64_t)count); StoreArrayLength(array);
        }
        code.Get(header);
        if (array->arr->akind == A_LIMITED) {
            code.I32((int32_t)IntSize(LenStore(array->arr))); code.Byte(0x6a);
        }
        code.Byte(0xad); code.Set(base);
    } else {
        auto identity = Local(WasmModule::I32), saved = Local(WasmModule::I32);
        if (memory >= 0) code.I32(memory);
        else StackIndex(storage.owners.at(owner) + 1);
        code.Set(identity);
        auto bytes = prefix + (uint32_t)count;
        if (memory >= 0) { code.I32((int32_t)bytes); code.Call(memories->Reserve(memory)); }
        else { code.Get(identity); code.I32((int32_t)bytes); code.Call(memories->ReserveDynamic()); }
        code.Set(saved);
        if (!owner->isglobal) {
            assert(!scopes.empty());
            scopes.back().push_back({nullptr, memory >= 0 ? (uint32_t)memory : identity, saved, memory < 0});
        }
        code.Get(identity); code.Byte(0xad); code.I64(32); code.Byte(0x86);
        code.Get(saved); code.Byte(0xad); code.Byte(0x84); code.Set(base);
        if (VariableArray(array)) {
            code.Get(base); Write(slot);
            code.Get(base); code.I64((int64_t)count); StoreArrayLength(array, memory);
        } else {
            Address(slot); code.Get(base); code.Mem(0x37);
            Address(slot); code.I64((int64_t)count); code.Mem(0x37, 0, 8);
        }
        if (prefix) { code.Get(base); code.I64(prefix); code.Byte(0x7c); code.Set(base); }
    }
    if (!count) return;
    auto source = module.Data(literal->val);
    code.Get(base);
    if (memory >= 0) code.Byte(0xa7);
    code.I32((int32_t)source); code.I32((int32_t)count);
    if (memory >= 0) { code.Byte(0xfc); code.U(10); code.U((uint32_t)memory); code.U(0); }
    else code.Call(memories->CopyFromFrame());
}

inline void WasmCodeGen::InitFilledArray(VarDef *owner, const Slot &slot, ArrayLit *literal) {
    auto array = owner->type, element = array->arr->sub;
    auto countnode = Is<IntLit>(literal->fillcount);
    if (!countnode || countnode->val < 0)
        Fail(literal->line, "array fill needs a nonnegative constant count");
    auto count = (uint64_t)countnode->val;
    auto stride = Size(element);
    auto prefix = VariableArray(array) ? (uint32_t)IntSize(LenStore(array->arr)) : 0u;
    if (count > (UINT32_MAX - prefix) / stride)
        Fail(owner->line, "array allocation exceeds memory32");
    if (prefix && prefix < 8 && count > ((1ull << (prefix * 8)) - 1))
        Fail(owner->line, "array length exceeds its stored prefix");
    auto memory = InlineArray(array) ? 0 : storage.Memory(owner, current);
    auto base = Local(WasmModule::I64);
    if (InlineArray(array)) {
        auto capacity = (uint64_t)ArrSize(array->arr);
        if (count > capacity || (array->arr->akind == A_FIXED && count != capacity))
            Fail(owner->line, "array fill does not fit its static layout");
        auto header = Local(WasmModule::I32); Address(slot); code.Set(header);
        if (array->arr->akind == A_LIMITED) {
            code.Get(header); code.I64((int64_t)count); StoreArrayLength(array);
        }
        code.Get(header);
        if (array->arr->akind == A_LIMITED) {
            code.I32((int32_t)IntSize(LenStore(array->arr))); code.Byte(0x6a);
        }
        code.Byte(0xad); code.Set(base);
    } else {
        auto bytes = prefix + (uint32_t)count * stride;
        auto identity = Local(WasmModule::I32), saved = Local(WasmModule::I32);
        if (memory >= 0) code.I32(memory);
        else StackIndex(storage.owners.at(owner) + 1);
        code.Set(identity);
        if (memory >= 0) { code.I32((int32_t)bytes); code.Call(memories->Reserve(memory)); }
        else { code.Get(identity); code.I32((int32_t)bytes); code.Call(memories->ReserveDynamic()); }
        code.Set(saved);
        if (!owner->isglobal) {
            assert(!scopes.empty());
            scopes.back().push_back({nullptr, memory >= 0 ? (uint32_t)memory : identity, saved, memory < 0});
        }
        code.Get(identity); code.Byte(0xad); code.I64(32); code.Byte(0x86);
        code.Get(saved); code.Byte(0xad); code.Byte(0x84); code.Set(base);
        if (VariableArray(array)) {
            code.Get(base); Write(slot);
            code.Get(base); code.I64((int64_t)count); StoreArrayLength(array, memory);
        } else {
            Address(slot); code.Get(base); code.Mem(0x37);
            Address(slot); code.I64((int64_t)count); code.Mem(0x37, 0, 8);
        }
    }
    // The language evaluates even a zero-count fill once. Capturing before
    // the loop also keeps reference targets and call side effects stable.
    auto item = Temp(element);
    Gen(literal->fillval); Convert(literal->fillval->exprtype, element); code.Set(item);
    if (!count) return;
    auto position = Local(WasmModule::I64); code.I64(0); code.Set(position);
    auto done = Open(), head = Open(0x03);
    code.Get(position); code.I64((int64_t)count); code.Byte(0x5a); Branch(done, true);
    // The whole payload was reserved, or is inside the checked activation
    // frame. The loop bounds prove that these additions cannot wrap.
    code.Get(base);
    if (memory >= 0) {
        code.Byte(0xa7); code.Get(position); code.Byte(0xa7);
        code.I32((int32_t)stride); code.Byte(0x6c); code.Byte(0x6a);
        if (prefix) { code.I32((int32_t)prefix); code.Byte(0x6a); }
        code.Get(item); StoreFixed(element, (uint32_t)memory);
    } else {
        code.Get(position); code.I64(stride); code.Byte(0x7e); code.Byte(0x7c);
        if (prefix) { code.I64(prefix); code.Byte(0x7c); }
        code.Get(item); Store(element);
    }
    code.Get(position); code.I64(1); code.Byte(0x7c); code.Set(position);
    Branch(head); Close(); Close();
}

inline void WasmCodeGen::InitVariableArray(VarDef *owner, const Slot &slot, ArrayLit *literal) {
    auto array = owner->type, element = array->arr->sub;
    auto prefix = (uint32_t)IntSize(LenStore(array->arr)), stride = Size(element);
    auto count = literal->elems.size();
    if (count > (UINT32_MAX - prefix) / stride)
        Fail(owner->line, "array allocation exceeds memory32");
    if (prefix < 8 && count > ((1ull << (prefix * 8)) - 1))
        Fail(owner->line, "array length exceeds its stored prefix");
    auto bytes = prefix + (uint32_t)count * stride;
    auto memory = storage.Memory(owner, current);
    auto identity = Local(WasmModule::I32), saved = Local(WasmModule::I32);
    if (memory >= 0) code.I32(memory);
    else StackIndex(storage.owners.at(owner) + 1);
    code.Set(identity);
    if (memory >= 0) { code.I32((int32_t)bytes); code.Call(memories->Reserve(memory)); }
    else { code.Get(identity); code.I32((int32_t)bytes); code.Call(memories->ReserveDynamic()); }
    code.Set(saved);
    if (!owner->isglobal) {
        assert(!scopes.empty());
        scopes.back().push_back({nullptr, memory >= 0 ? (uint32_t)memory : identity, saved, memory < 0});
    }
    auto header = Local(WasmModule::I64);
    code.Get(identity); code.Byte(0xad); code.I64(32); code.Byte(0x86);
    code.Get(saved); code.Byte(0xad); code.Byte(0x84); code.Set(header);
    code.Get(header); Write(slot);
    code.Get(header); code.I64((int64_t)count); StoreArrayLength(array, memory);
    // The complete payload is reserved before initializers call other code.
    // Their stack bases are above this live owner in the storage plan.
    if (!count) return;
    auto item = Temp(element);
    for (size_t i = 0; i < count; i++) {
        auto value = literal->elems[i]; Gen(value); Convert(value->exprtype, element);
        code.Set(item);
        auto offset = prefix + (uint32_t)i * stride;
        // Reserve checked saved + bytes before any initializer ran. Each
        // constant offset lies inside that reservation, so neither addition
        // can wrap the low Memory32 address or carry into the memory id.
        if (memory >= 0) {
            code.Get(saved); code.I32((int32_t)offset); code.Byte(0x6a); code.Get(item);
            StoreFixed(element, (uint32_t)memory);
        } else {
            code.Get(header); code.I64(offset); code.Byte(0x7c); code.Get(item); Store(element);
        }
    }
}

inline void WasmCodeGen::InitArray(VarDef *owner, const Slot &slot, Node *init) {
    if (owner->reusable) Fail(owner->line, "pool owners need the pending descriptor lowering");
    while (auto call = Is<Call>(init)) {
        if (!call->defaultinit) break;
        init = call->defaultinit;
    }
    if (auto literal = Is<StrLit>(init)) { InitByteString(owner, slot, literal); return; }
    auto literal = Is<ArrayLit>(init);
    if (!literal || literal->capexpr)
        Fail(init->line, "this array constructor needs the pending destination lowering");
    auto array = owner->type;
    if (literal->fillval) { InitFilledArray(owner, slot, literal); return; }
    if (VariableArray(array)) { InitVariableArray(owner, slot, literal); return; }
    if (!IsResz(array)) {
        auto header = Local(WasmModule::I32);
        Address(slot); code.Set(header);
        if (array->arr->akind == A_FIXED) {
            if ((uint64_t)ArrSize(array->arr) != literal->elems.size())
                Fail(init->line, "this fixed array constructor needs the pending destination lowering");
            auto element = array->arr->sub;
            for (size_t i = 0; i < literal->elems.size(); i++) {
                code.Get(header); code.I32((int32_t)(i * Size(element))); code.Byte(0x6a);
                auto value = literal->elems[i]; Gen(value); Convert(value->exprtype, element);
                StoreFixed(element);
            }
        } else {
            code.Get(header); code.I64(0); StoreArrayLength(array);
            for (auto value : literal->elems)
                PushArray(header, array, value, nullptr, value->line, 0);
        }
        return;
    }
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
        PushArray(header, array, value, nullptr, value->line, memory);
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

inline void WasmCodeGen::PushArray(uint32_t header, TypeExpr *array, Node *value,
                                  TypeExpr *result, Line line, int memory) {
    auto element = array->arr->sub;
    Gen(value); Convert(value->exprtype, element);
    auto item = Temp(element); code.Set(item);
    // Read the current header after argument effects. A call used for the
    // value can itself append through another reference to this owner.
    auto length = Local(WasmModule::I64), old = Local(WasmModule::I32);
    ArrayLength(header, array); code.Set(length);
    if (IsResz(array)) {
        if (memory >= 0) { code.I32((int32_t)Size(element)); code.Call(memories->Reserve(memory)); }
        else {
            code.Get(header); code.Mem(0x29); code.I64(32); code.Byte(0x88); code.Byte(0xa7);
            code.I32((int32_t)Size(element)); code.Call(memories->ReserveDynamic());
        }
        code.Set(old);
        code.Get(header); code.Mem(0x29); code.I64(-4294967296ll); code.Byte(0x83);
        code.Get(old); code.Byte(0xad); code.Byte(0x84);
    } else {
        code.Get(length); code.I64(ArrSize(array->arr)); code.Byte(0x5a);
        Open(0x04); Trap(10, line); Close();
        ElementOffset(header, length, array, line);
    }
    auto address = Local(WasmModule::I64); code.Tee(address); code.Get(item); StoreElement(element, memory);
    code.Get(header); code.Get(length); code.I64(1); code.Byte(0x7c); StoreArrayLength(array);
    if (!Void(result)) {
        code.Get(address);
        if (result->kind != TY_REF || !TEq(result->ref->sub, element)) {
            LoadElement(element, memory); Convert(element, result);
        } else if (Type(result) == WasmModule::I32) code.Byte(0xa7);
    }
    (void)line;
}

inline void WasmCodeGen::ElementOffset(uint32_t header, uint32_t index, TypeExpr *array, Line line) {
    auto element = array->arr->sub;
    auto base = Local(WasmModule::I64), offset = Local(WasmModule::I64);
    code.Get(header);
    if (IsResz(array)) code.Mem(0x29);
    else if (!VariableArray(array)) {
        if (array->arr->akind == A_LIMITED) {
            code.I32((int32_t)IntSize(LenStore(array->arr))); code.Byte(0x6a);
        }
        code.Byte(0xad);
    }
    code.Set(base);
    code.Get(base); code.I64(UINT32_MAX); code.Byte(0x83);
    if (VariableArray(array)) { code.I64(IntSize(LenStore(array->arr))); code.Byte(0x7c); }
    code.Get(index); code.I64(Size(element)); code.Byte(0x7e); code.Byte(0x7c); code.Tee(offset);
    code.I64(UINT32_MAX); code.Byte(0x56); Open(0x04); Trap(11, line); Close();
    code.Get(base); code.I64(-4294967296ll); code.Byte(0x83); code.Get(offset); code.Byte(0x84);
}

inline pair<TypeExpr *, int> WasmCodeGen::ElementAddress(Index *index) {
    auto array = ArrayType(index->obj), element = array->arr->sub;
    auto header = ArrayHeader(index->obj);
    // C's IndexLoc snapshots the view before an index with statement
    // effects. Snapshot its length here as well; bases remain stable.
    auto length = Local(WasmModule::I64), position = Local(WasmModule::I64);
    ArrayLength(header, array, ArrayMemory(index->obj)); code.Set(length);
    Gen(index->idx); code.Set(position);
    if (!index->nobc) {
        code.Get(position); code.Get(length); code.Byte(0x5a);
        Open(0x04); Trap(8, index->line); Close();
    }
    ElementOffset(header, position, array, index->line);
    return {element, ArrayMemory(index->obj)};
}

inline void WasmCodeGen::AssignElement(Index *index, Node *rhs, TType op, bool pointee, Line line) {
    auto [type, memory] = ElementAddress(index);
    auto address = Local(WasmModule::I64); code.Set(address);
    if (pointee && type->kind == TY_REF && op != T_DOTASSIGN) {
        code.Get(address); LoadElement(type, memory); CheckNull(line, Type(type));
        if (type->ref->sub->kind == TY_ARRAY) Fail(line, "whole-array assignment needs the pending destination lowering");
        if (Type(type) == WasmModule::I32) address = Local(WasmModule::I32);
        code.Set(address); type = type->ref->sub; memory = -1;
    }
    if (op == T_DOTASSIGN) {
        if (type->kind != TY_REF) Fail(line, "reference rebinding requires a reference element");
        if (auto source = Is<Ident>(rhs); source && source->vdef && source->vdef->type->kind != TY_REF) {
            ReferenceAddress(Find(source->vdef));
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
    auto array = ArrayType(arguments[0]), element = array->arr->sub;
    auto header = ArrayHeader(arguments[0]);
    auto memory = ArrayMemory(arguments[0]);
    if (call->builtin == B_LEN) { ArrayLength(header, array, memory); return; }
    if (VariableArray(array)) Fail(call->line, "variable-array mutation needs the pending destination lowering");
    if (call->builtin == B_CAP) { code.I64(ArrSize(array->arr)); return; }
    if (call->builtin == B_PUSH) {
        PushArray(header, array, arguments[1], call->exprtype, call->line, memory); return;
    }
    auto length = Local(WasmModule::I64);
    ArrayLength(header, array); code.Set(length);
    if (call->builtin == B_POP) {
        code.Get(length); code.Byte(0x50); Open(0x04); Trap(9, call->line); Close();
        code.Get(length); code.I64(1); code.Byte(0x7d); code.Set(length);
    } else { code.I64(0); code.Set(length); }
    ElementOffset(header, length, array, call->line);
    auto address = Local(WasmModule::I64); code.Set(address);
    int result = -1;
    if (call->builtin == B_POP) {
        result = (int)Temp(element); code.Get(address); LoadElement(element, memory); code.Set(result);
    }
    if (IsResz(array) && memory >= 0) { code.Get(address); code.Byte(0xa7); code.Byte(0x24); code.U(memory); }
    else if (IsResz(array)) {
        code.Get(header); code.Mem(0x29); code.I64(32); code.Byte(0x88); code.Byte(0xa7);
        code.Get(address); code.Byte(0xa7); code.Call(memories->Top(true));
    }
    code.Get(header); code.Get(length); StoreArrayLength(array);
    if (result >= 0) { code.Get(result); Convert(element, call->exprtype); }
}

inline void WasmCodeGen::ArrayEquality(Binary *node) {
    if (ArrayPathHasStatements(node->right))
        Fail(node->line, "effectful array comparison needs the pending destination lowering");
    auto lefttype = ArrayType(node->left), righttype = ArrayType(node->right);
    auto element = lefttype->arr->sub;
    auto left = ArrayHeader(node->left), length = Local(WasmModule::I64);
    ArrayLength(left, lefttype, ArrayMemory(node->left)); code.Set(length);
    auto right = ArrayHeader(node->right);
    auto result = Local(WasmModule::I32), position = Local(WasmModule::I64);
    code.I32(0); code.Set(result);
    code.Get(length); ArrayLength(right, righttype, ArrayMemory(node->right)); code.Byte(0x51); Open(0x04);
    code.I32(1); code.Set(result); code.I64(0); code.Set(position);
    auto done = Open(), head = Open(0x03);
    code.Get(position); code.Get(length); code.Byte(0x5a); Branch(done, true);
    ElementOffset(left, position, lefttype, node->line);
    LoadElement(element, ArrayMemory(node->left));
    ElementOffset(right, position, righttype, node->line);
    LoadElement(righttype->arr->sub, ArrayMemory(node->right));
    auto type = Type(element);
    code.Byte(type == WasmModule::F32 ? 0x5b : type == WasmModule::F64 ? 0x61 :
              type == WasmModule::I32 ? 0x46 : 0x51);
    code.Byte(0x45); Open(0x04);
    code.I32(0); code.Set(result); Branch(done); Close();
    code.Get(position); code.I64(1); code.Byte(0x7c); code.Set(position);
    Branch(head); Close(); Close(); Close();
    code.Get(result);
    if (node->op == T_NEQ) code.Byte(0x45);
}

inline bool WasmCodeGen::ArrayPathHasStatements(Node *n) {
    if (!n) return false;
    if (Is<Call>(n) || Is<Block>(n) || Is<IfExpr>(n) || Is<MatchExpr>(n) ||
        Is<LoopExpr>(n) || Is<EarlyBlock>(n) || Is<InlineBlock>(n) || Is<StrLit>(n)) return true;
    auto found = false;
    n->Children([&](Node *child) { found = found || ArrayPathHasStatements(child); });
    return found;
}

inline void WasmCodeGen::CaptureArrayWalk(Node *n, ArrayWalk &walk) {
    if (auto index = Is<Index>(n)) {
        CaptureArrayWalk(index->obj, walk);
        ArrayWalkStep step {index, Local(WasmModule::I64)};
        if (ArrayPathHasStatements(index->idx)) {
            // Native IndexLoc freezes the parent view before an index that
            // emits statements. References below that view still reload.
            auto parent = LoadArrayWalk(walk);
            step.length = Local(WasmModule::I64);
            ArrayLength(parent, ArrayType(index->obj), ArrayMemory(index->obj)); code.Set(step.length);
            walk.root = nullptr; walk.header = parent; walk.steps.clear();
        }
        Gen(index->idx); code.Set(step.position);
        walk.steps.push_back(step);
        return;
    }
    if (auto u = Is<Unary>(n); u && u->op == T_BITAND && u->child->exprtype->kind != TY_REF &&
        (Is<Ident>(u->child) || Is<Index>(u->child))) {
        CaptureArrayWalk(u->child, walk); return;
    }
    auto id = Is<Ident>(n);
    if (id && id->vdef && id->vdef->isvar && id->vdef->type->kind == TY_REF) walk.root = n;
    else walk.header = ArrayHeader(n); // A call or temporary is evaluated once.
}

inline uint32_t WasmCodeGen::LoadArrayWalk(const ArrayWalk &walk) {
    auto header = walk.root ? ArrayHeader(walk.root) : walk.header;
    for (auto &step : walk.steps) {
        auto index = step.node;
        auto array = ArrayType(index->obj), element = array->arr->sub;
        if (element->kind != TY_REF || element->ref->sub->kind != TY_ARRAY)
            Fail(index->line, "this array path needs the pending compound lowering");
        if (!index->nobc) {
            code.Get(step.position);
            if (step.length != UINT32_MAX) code.Get(step.length);
            else ArrayLength(header, array, ArrayMemory(index->obj));
            code.Byte(0x5a); Open(0x04); Trap(8, index->line); Close();
        }
        ElementOffset(header, step.position, array, index->line);
        LoadElement(element, ArrayMemory(index->obj)); CheckNull(index->line, Type(element));
        header = Local(Type(element)); code.Set(header);
    }
    return header;
}

inline void WasmCodeGen::ArrayFor(ForLoop *loop) {
    auto array = ArrayType(loop->iter), element = array->arr->sub;
    auto id = Is<Ident>(loop->iter);
    auto reload = id && id->vdef && id->vdef->isvar && id->vdef->type->kind == TY_REF;
    optional<ArrayWalk> walk;
    if (Is<Index>(loop->iter)) { walk.emplace(); CaptureArrayWalk(loop->iter, *walk); }
    auto header = reload || walk ? Local(Type(array)) : ArrayHeader(loop->iter);
    auto memory = ArrayMemory(loop->iter);
    auto position = Local(WasmModule::I64); code.I64(0); code.Set(position);
    auto end = Open(), head = Open(0x03);
    if (walk) {
        auto currentheader = LoadArrayWalk(*walk); code.Get(currentheader); code.Set(header);
    } else if (reload) {
        auto currentheader = ArrayHeader(loop->iter); code.Get(currentheader); code.Set(header);
    }
    // Growth during iteration is permitted. Read the current count on each
    // test rather than assuming the entry view has a fixed length.
    code.Get(position); ArrayLength(header, array, memory); code.Byte(0x5a); Branch(end, true);
    ElementOffset(header, position, array, loop->line);
    if (!loop->byref || element->kind == TY_REF) {
        LoadElement(element, memory); Convert(element, loop->vdef->type);
    } else if (Type(loop->vdef->type) == WasmModule::I32) code.Byte(0xa7);
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
