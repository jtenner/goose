// Stored fixed values have places, not scalar Wasm values.
#pragma once

namespace goose {

inline TypeExpr *WasmCodeGen::ActualType(Node *n) {
    if (auto id = Is<Ident>(n); id && id->vdef) return id->vdef->type;
    if (auto field = Is<Dot>(n); field && field->IsField()) {
        auto t = ActualType(field->obj);
        while (t->kind == TY_REF) t = t->ref->sub;
        if (t->kind != TY_STRUCT) Fail(n->line, "this field receiver needs the pending layout lowering");
        auto si = SI(t);
        if (field->fieldidx < 0 || (size_t)field->fieldidx >= si->ftypes.size() || !si->ftypes[field->fieldidx])
            Fail(n->line, "this field selector needs the pending layout lowering");
        return si->ftypes[field->fieldidx];
    }
    if (auto index = Is<Index>(n)) {
        auto t = ActualType(index->obj);
        while (t->kind == TY_REF) t = t->ref->sub;
        if (t->kind == TY_ARRAY) return t->arr->sub;
    }
    if (auto address = Is<Unary>(n); address && address->op == T_BITAND) {
        auto t = ActualType(address->child);
        return t;
    }
    if (auto call = Is<Call>(n)) {
        auto &rets = call->spec ? call->spec->rets : call->rettypes;
        if (rets.size() == 1) return rets[0];
    }
    if (auto inlined = Is<InlineBlock>(n); inlined && inlined->spec->rets.size() == 1)
        return inlined->spec->rets[0];
    return n->exprtype;
}

inline WasmCodeGen::FixedPlace WasmCodeGen::OwnerPlace(VarDef *owner) {
    auto &slot = Find(owner);
    if (!slot.memory) Fail(owner->line, "fixed owner is missing planned storage");
    auto address = Local(WasmModule::I32); Address(slot); code.Set(address);
    return {owner->type, address, 0, 0, false, true};
}

inline void WasmCodeGen::PlaceAddress(const FixedPlace &p, uint8_t representation, Line line) {
    if (representation == WasmModule::I32) {
        if (p.memory > 0) Fail(line, "this thin reference requires memory zero");
        if (p.packed && p.memory < 0) {
            code.Get(p.address); code.I64(32); code.Byte(0x88); code.Byte(0x50); code.Byte(0x45);
            Open(0x04); Trap(7, line); Close();
        }
    }
    if (!p.packed && p.bounded) {
        code.Get(p.address);
        if (p.offset) { code.I32((int32_t)p.offset); code.Byte(0x6a); }
        if (representation == WasmModule::I64) {
            code.Byte(0xad);
            if (p.memory > 0) { code.I64((int64_t)p.memory << 32); code.Byte(0x84); }
        }
        return;
    }
    if (!p.offset) {
        code.Get(p.address);
        if (p.packed && representation == WasmModule::I32) code.Byte(0xa7);
        else if (!p.packed && representation == WasmModule::I64) code.Byte(0xad);
        return;
    }
    if (fixedoffsetscratch == UINT32_MAX) fixedoffsetscratch = Local(WasmModule::I64);
    code.Get(p.address);
    if (p.packed) { code.I64(UINT32_MAX); code.Byte(0x83); }
    else code.Byte(0xad);
    code.I64(p.offset); code.Byte(0x7c); code.Tee(fixedoffsetscratch);
    code.I64(UINT32_MAX); code.Byte(0x56); Open(0x04); Trap(11, line); Close();
    if (representation == WasmModule::I64 && p.packed) {
        code.Get(p.address); code.I64(-4294967296ll); code.Byte(0x83);
        code.Get(fixedoffsetscratch); code.Byte(0x84);
    } else {
        code.Get(fixedoffsetscratch);
        if (representation == WasmModule::I32) code.Byte(0xa7);
    }
}

inline void WasmCodeGen::StoreAddress(const FixedPlace &p) {
    if (p.memory >= 0) {
        code.Get(p.address);
        if (p.packed) code.Byte(0xa7);
    } else PlaceAddress(p, WasmModule::I64, p.type->line);
}

inline void WasmCodeGen::ReadPlace(const FixedPlace &p) {
    if (Aggregate(p.type)) Fail(p.type->line, "aggregate reads need a stored-value consumer");
    StoreAddress(p);
    if (p.memory >= 0) LoadFixed(p.type, (uint32_t)p.memory, p.offset);
    else Load(p.type);
}

inline void WasmCodeGen::StorePlace(const FixedPlace &p) {
    if (Aggregate(p.type)) Fail(p.type->line, "whole-aggregate assignment needs the pending destination lowering");
    if (p.memory >= 0) StoreFixed(p.type, (uint32_t)p.memory, p.offset);
    else Store(p.type);
}

inline WasmCodeGen::FixedPlace WasmCodeGen::PointeePlace(TypeExpr *reference, Line line) {
    assert(reference->kind == TY_REF);
    auto rep = Type(reference);
    auto address = Local(rep);
    code.Tee(address); code.Byte(rep == WasmModule::I64 ? 0x50 : 0x45);
    Open(0x04); Trap(4, line); Close();
    return {reference->ref->sub, address, 0, rep == WasmModule::I64 ? -1 : 0,
            rep == WasmModule::I64, false};
}

inline WasmCodeGen::FixedPlace WasmCodeGen::DereferencePlace(FixedPlace p, Line line) {
    assert(p.type->kind == TY_REF);
    ReadPlace(p);
    return PointeePlace(p.type, line);
}

inline WasmCodeGen::FixedPlace WasmCodeGen::ResolvePlace(Node *n) {
    FixedPlace place {nullptr, 0};
    if (auto id = Is<Ident>(n); id && id->vdef) {
        auto &slot = Find(id->vdef);
        if (slot.type->kind == TY_REF) {
            Read(slot); place = PointeePlace(slot.type, n->line);
        } else if (DataArray(slot.type)) {
            auto address = Local(WasmModule::I64); Read(slot); code.Set(address);
            place = {slot.type, address, 0, storage.Memory(id->vdef, current), true, true};
        } else place = OwnerPlace(id->vdef);
    } else if (auto field = Is<Dot>(n); field && field->IsField()) place = FieldPlace(field);
    else if (auto index = Is<Index>(n)) {
        auto element = ElementAddress(index);
        auto address = Local(WasmModule::I64); code.Set(address);
        place = {element.first, address, 0, element.second, true, true};
    } else if (auto address = Is<Unary>(n); address && address->op == T_BITAND)
        return ResolvePlace(address->child);
    else if (Is<Call>(n) || Is<InlineBlock>(n)) {
        auto actual = ActualType(n);
        if (!actual || actual->kind != TY_REF)
            Fail(n->line, "aggregate results need the pending destination lowering");
        Gen(n, actual); place = PointeePlace(actual, n->line);
    } else Fail(n->line, "aggregate temporaries need the pending destination lowering");
    while (place.type->kind == TY_REF) place = DereferencePlace(place, n->line);
    return place;
}

inline WasmCodeGen::FixedPlace WasmCodeGen::FieldPlace(Dot *field) {
    auto object = ResolvePlace(field->obj);
    if (object.type->kind != TY_STRUCT) Fail(field->line, "this field receiver needs the pending layout lowering");
    RequireFixed(object.type, field->line);
    auto si = SI(object.type);
    if (field->accessorowner && SI(field->accessorowner) != si)
        Fail(field->line, "field adaptation needs the pending layout lowering");
    auto type = ActualType(field);
    auto offset = StructLayout(si).offs[field->fieldidx];
    if ((uint64_t)offset > UINT32_MAX - object.offset) Fail(field->line, "field offset exceeds memory32");
    object.offset += (uint32_t)offset; object.type = type;
    return object;
}

inline void WasmCodeGen::AssignField(Dot *field, Node *rhs, TType op, bool pointee, Line line) {
    auto place = FieldPlace(field);
    if (op == T_DOTASSIGN) {
        if (place.type->kind != TY_REF) Fail(line, "reference rebinding requires a reference field");
        StoreAddress(place);
        if (ActualType(rhs)->kind != TY_REF && (Is<Ident>(rhs) || Is<Dot>(rhs) || Is<Index>(rhs)))
            PlaceAddress(ResolvePlace(rhs), Type(place.type), line);
        else ReferenceValue(rhs, Type(place.type));
        StorePlace(place); return;
    }
    if (pointee && place.type->kind == TY_REF) place = DereferencePlace(place, line);
    if (Aggregate(place.type)) Fail(line, "whole-aggregate assignment needs the pending destination lowering");
    StoreAddress(place);
    if (op != T_ASSIGN) ReadPlace(place);
    if (rhs) { Gen(rhs); Convert(rhs->exprtype, place.type); }
    else if (place.type->kind == TY_FLT) {
        if (place.type->fltstorage == FS_F32) code.F32(1); else code.F64(1);
    } else code.I64(1);
    if (op != T_ASSIGN) Arithmetic(op, place.type, line);
    StorePlace(place);
}

inline void WasmCodeGen::InlineArrayLiteral(TypeExpr *array, uint32_t header, ArrayLit *literal, bool reuse) {
    if (array->arr->akind == A_FIXED) {
        if ((uint64_t)ArrSize(array->arr) != literal->elems.size())
            Fail(literal->line, "this fixed array constructor needs the pending destination lowering");
        auto element = array->arr->sub;
        for (size_t i = 0; i < literal->elems.size(); i++) {
            code.Get(header); code.I32((int32_t)(i * Size(element))); code.Byte(0x6a);
            auto value = literal->elems[i]; Gen(value); Convert(value->exprtype, element);
            StoreFixed(element);
        }
    } else {
        code.Get(header); code.I64(0); StoreArrayLength(array);
        optional<PushScratch> scratch;
        if (reuse && !literal->elems.empty())
            scratch = PushScratch {Temp(array->arr->sub), Local(WasmModule::I64),
                                   Local(WasmModule::I32), Local(WasmModule::I64),
                                   Local(WasmModule::I64), Local(WasmModule::I64)};
        for (auto value : literal->elems)
            PushArray(header, array, value, nullptr, value->line, 0, scratch ? &*scratch : nullptr);
    }
}

inline void WasmCodeGen::ConstructFixed(FixedPlace destination, Node *source) {
    if (destination.memory != 0 || !destination.bounded)
        Fail(source->line, "fixed construction needs a fresh planned destination");
    auto type = destination.type;
    if (type->kind == TY_ARRAY && !InlineArray(type))
        Fail(source->line, "nonfixed fields need the pending destination lowering");
    auto bytes = RequireFixed(type, source->line);
    auto zero = [&](uint32_t count) {
        if (!count) return;
        PlaceAddress(destination, WasmModule::I32, source->line);
        code.I32(0); code.I32((int32_t)count); code.Fill(0);
    };
    while (auto call = Is<Call>(source)) {
        if (call->builtin == B_COPY) { source = call->ValueArgNodes().at(0); continue; }
        if (call->builtin != B_DEFAULT) break;
        if (type->kind == TY_STRUCT && call->defaultinit) { source = call->defaultinit; continue; }
        if (InlineArray(type)) {
            if (type->arr->akind == A_FIXED) zero(bytes);
            else {
                StoreAddress(destination); code.I64(0);
                StoreArrayField(type, 0, destination.offset);
            }
            return;
        }
        Fail(source->line, "this default needs the pending destination lowering");
    }
    if (type->kind == TY_STRUCT) if (auto literal = Is<StructLit>(source)) {
        auto si = SI(type);
        if (literal->sinst != si) Fail(source->line, "aggregate adaptation needs the pending destination lowering");
        if (LastRealField(si->st->fields) < 0) { zero(bytes); return; }
        auto &offsets = StructLayout(si).offs;
        size_t next = 0;
        for (size_t i = 0; i < si->ftypes.size(); i++) {
            auto ft = si->ftypes[i];
            if (!ft) continue;
            while (next < literal->fieldindices.size() && literal->fieldindices[next] < (int)i) next++;
            auto init = next < literal->fieldindices.size() && literal->fieldindices[next] == (int)i
                          ? literal->inits[next++].val : nullptr;
            auto child = destination;
            child.type = ft;
            if ((uint64_t)offsets[i] > UINT32_MAX - child.offset) Fail(source->line, "field offset exceeds memory32");
            child.offset += (uint32_t)offsets[i];
            if (Aggregate(ft)) {
                if (!init) Fail(source->line, "missing checked aggregate initializer");
                ConstructFixed(child, init);
            } else {
                StoreAddress(child);
                if (init) { Gen(init); Convert(init->exprtype, ft); }
                else {
                    if (ft->kind != TY_REF || !ft->ref->optional) Fail(source->line, "missing checked field initializer");
                    if (Type(ft) == WasmModule::I64) code.I64(0); else code.I32(0);
                }
                StorePlace(child);
            }
        }
        return;
    }
    if (InlineArray(type)) {
        if (auto text = Is<StrLit>(source)) { InitByteString(nullptr, nullptr, text, &destination); return; }
        if (auto literal = Is<ArrayLit>(source)) {
            if (literal->capexpr) Fail(source->line, "this capacity constructor needs the pending destination lowering");
            if (literal->fillval) { InitFilledArray(nullptr, nullptr, literal, &destination); return; }
            auto header = Local(WasmModule::I32);
            PlaceAddress(destination, WasmModule::I32, source->line); code.Set(header);
            InlineArrayLiteral(type, header, literal, true); return;
        }
    }
    auto from = ActualType(source);
    while (from && from->kind == TY_REF) from = from->ref->sub;
    if (!from || !TEq(type, from)) Fail(source->line, "aggregate adaptation needs the pending destination lowering");
    auto existing = ResolvePlace(source);
    auto dest = Local(WasmModule::I64), src = Local(WasmModule::I64), length = Local(WasmModule::I32);
    PlaceAddress(destination, WasmModule::I64, source->line); code.Set(dest);
    PlaceAddress(existing, WasmModule::I64, source->line); code.Set(src);
    code.I32((int32_t)bytes); code.Set(length);
    if (bytes) CopyBytes(dest, 0, src, existing.memory, length);
}

inline bool WasmCodeGen::FieldPath(Node *n) {
    if (auto field = Is<Dot>(n)) return field->IsField();
    if (auto index = Is<Index>(n)) return FieldPath(index->obj);
    if (auto address = Is<Unary>(n); address && address->op == T_BITAND) return FieldPath(address->child);
    return false;
}

}  // namespace goose
