// Stored fixed values have places, not scalar Wasm values.
#pragma once

namespace goose {

inline TypeExpr *WasmCodeGen::ActualType(Node *n) {
    if (auto id = Is<Ident>(n); id && id->vdef) return id->vdef->type;
    if (auto field = Is<Dot>(n); field && field->IsField()) {
        auto t = ActualType(field->obj);
        while (t->kind == TY_REF) t = t->ref->sub;
        return StoredField(t, field->fieldidx, n->line).first;
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

inline WasmCodeGen::FreshFixedDestination WasmCodeGen::FreshOwner(VarDef *owner, Node *initialization) {
    auto image = RequireFixed(owner->type, owner->line);
    if (Nominal(owner->type)) {
        auto it = storage.fixedvalues.find(owner);
        if (it == storage.fixedvalues.end() || it->second.initialization != initialization ||
            it->second.argument || !it->second.initialized || it->second.image != image)
            Fail(owner->line, "fixed construction needs its planned fresh owner");
    } else {
        auto declaration = Is<VarDecl>(initialization);
        if (!InlineArray(owner->type) || !declaration || declaration->inline_arg ||
            find(declaration->defs.begin(), declaration->defs.end(), owner) == declaration->defs.end())
            Fail(owner->line, "fixed construction needs its planned fresh owner");
    }
    return {OwnerPlace(owner), owner, 0, image};
}

inline WasmCodeGen::FreshFixedDestination WasmCodeGen::FixedChild(
        FreshFixedDestination parent, TypeExpr *type, uint32_t offset, Line line) {
    auto image = RequireFixed(type, line);
    if (offset > parent.image || image > parent.image - offset ||
        offset > UINT32_MAX - parent.place.offset || offset > UINT32_MAX - parent.rootOffset)
        Fail(line, "fixed child exceeds its planned owner image");
    parent.place.offset += offset; parent.place.type = type;
    parent.rootOffset += offset; parent.image = image;
    return parent;
}

inline WasmCodeGen::FixedFields WasmCodeGen::VariantFields(EnumInst *instance, int variant, Line line) {
    if (variant < 0 || (size_t)variant >= instance->en->variants.size() ||
        (size_t)variant >= instance->vftypes.size())
        Fail(line, "missing checked variant layout");
    return {instance->en->variants[variant].fields, instance->vftypes[variant],
            VariantLayout(instance, variant)};
}

inline WasmCodeGen::FixedFields WasmCodeGen::FieldsOf(TypeExpr *type, Line line) {
    RequireFixed(type, line);
    if (type->kind == TY_STRUCT) {
        auto si = SI(type);
        return {si->st->fields, si->ftypes, StructLayout(si)};
    }
    if (type->kind == TY_VARIANT) {
        auto ei = EIVar(type);
        return VariantFields(ei, ei->en->VariantIndex(type->var->variant), line);
    }
    Fail(line, "this field receiver needs the pending layout lowering");
}

inline pair<TypeExpr *, uint32_t> WasmCodeGen::StoredField(TypeExpr *type, int field, Line line) {
    auto view = FieldsOf(type, line);
    if (field < 0 || (size_t)field >= view.types.size() || !view.types[field])
        Fail(line, "this field selector needs the pending layout lowering");
    return {view.types[field], (uint32_t)view.layout.offs[field]};
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
        place = CaptureElementPlace(ElementAddress(index));
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
    auto [type, offset] = StoredField(object.type, field->fieldidx, field->line);
    if (field->accessorowner && !TEq(field->accessorowner, object.type))
        Fail(field->line, "field adaptation needs the pending layout lowering");
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

inline void WasmCodeGen::InlineArrayLiteral(const ArrayPlace &place, ArrayLit *literal, bool reuse) {
    auto array = place.layout.type;
    if (array->arr->akind == A_FIXED) {
        if ((uint64_t)ArrSize(array->arr) != literal->elems.size())
            Fail(literal->line, "this fixed array constructor needs the pending destination lowering");
        auto element = array->arr->sub;
        for (size_t i = 0; i < literal->elems.size(); i++) {
            EmitKnownOffset(place.image, (uint32_t)place.image.memory, literal->line);
            code.I32((int32_t)(i * place.layout.stride)); code.Byte(0x6a);
            auto value = literal->elems[i]; Gen(value); Convert(value->exprtype, element);
            StoreFixed(element, (uint32_t)place.elementMemory);
        }
    } else {
        PrepareArrayLengthStore(place); code.I64(0); StoreArrayLength(place);
        optional<PushScratch> scratch;
        if (reuse && !literal->elems.empty())
            scratch = PushScratch {Temp(array->arr->sub), Local(WasmModule::I64),
                                   Local(WasmModule::I32), Local(WasmModule::I64),
                                   Local(WasmModule::I64), Local(WasmModule::I64)};
        for (auto value : literal->elems)
            PushArray(place, value, nullptr, value->line, scratch ? &*scratch : nullptr);
    }
}

inline void WasmCodeGen::ConstructFields(FreshFixedDestination destination, StructLit *literal,
                                         const FixedFields &view, uint32_t prefix, Line line) {
    size_t next = 0;
    for (size_t i = 0; i < view.types.size(); i++) {
        auto ft = view.types[i];
        if (!ft) continue;
        while (next < literal->fieldindices.size() && literal->fieldindices[next] < (int)i) next++;
        auto init = next < literal->fieldindices.size() && literal->fieldindices[next] == (int)i
                        ? literal->inits[next++].val : nullptr;
        auto offset = (uint64_t)prefix + (uint64_t)view.layout.offs[i];
        if (offset > UINT32_MAX) Fail(line, "field offset exceeds memory32");
        auto child = FixedChild(destination, ft, (uint32_t)offset, line);
        if (Aggregate(ft)) {
            if (!init) Fail(line, "missing checked aggregate initializer");
            ConstructFixed(child, init);
        } else {
            StoreAddress(child.place);
            if (init) { Gen(init); Convert(init->exprtype, ft); }
            else {
                if (ft->kind != TY_REF || !ft->ref->optional) Fail(line, "missing checked field initializer");
                if (Type(ft) == WasmModule::I64) code.I64(0); else code.I32(0);
            }
            StorePlace(child.place);
        }
    }
}

inline void WasmCodeGen::ConstructAggregateArray(FreshFixedDestination destination, ArrayLit *literal) {
    auto array = destination.place.type;
    if (!InlineArray(array) || !Nominal(array->arr->sub))
        Fail(literal->line, "aggregate array construction needs a fixed Memory 0 destination");
    if (literal->fillval)
        Fail(literal->line, "aggregate array fills need the pending snapshot lowering");
    if (literal->capexpr)
        Fail(literal->line, "aggregate capacity constructors need the pending destination lowering");
    auto element = array->arr->sub;
    auto stride = RequireFixed(element, literal->line);
    if (!stride) Fail(literal->line, "zero-stride aggregate elements need the pending layout lowering");
    auto capacity = (uint64_t)ArrSize(array->arr);
    if (literal->elems.size() > capacity ||
        (array->arr->akind == A_FIXED && literal->elems.size() != capacity))
        Fail(literal->line, "aggregate literal exceeds its checked array extent");
    auto prefix = array->arr->akind == A_LIMITED ? (uint32_t)IntSize(LenStore(array->arr)) : 0u;
    if (prefix) {
        auto place = ArrayFromPlace(destination.place, literal->line);
        PrepareArrayLengthStore(place); code.I64((int64_t)literal->elems.size()); StoreArrayLength(place);
    }
    for (size_t i = 0; i < literal->elems.size(); i++) {
        auto offset = (uint64_t)prefix + i * (uint64_t)stride;
        if (offset > UINT32_MAX) Fail(literal->line, "aggregate element offset exceeds memory32");
        auto child = FixedChild(destination, element, (uint32_t)offset, literal->line);
        auto init = literal->elems[i];
        while (auto copy = Is<Call>(init)) {
            if (copy->builtin != B_COPY) break;
            init = copy->ValueArgNodes().at(0);
        }
        if (auto id = Is<Ident>(init); id && id->vdef && TEq(element, id->vdef->type)) {
            auto &source = Find(id->vdef);
            if (!source.memory) Fail(init->line, "fixed source owner is missing planned storage");
            EmitKnownOffset(child.place, (uint32_t)child.place.memory, init->line);
            Address(source); // A named fixed owner has a planned Memory 0 slot.
            code.I32((int32_t)stride); code.Copy((uint32_t)child.place.memory, 0);
        } else ConstructFixed(child, init);
    }
}

inline void WasmCodeGen::CopyFixed(FreshFixedDestination destination, FixedPlace source, Line line) {
    if (!TEq(destination.place.type, source.type))
        Fail(line, "aggregate adaptation needs the pending destination lowering");
    if (!destination.image) {
        // An empty standalone owner has an identity byte, but no payload image.
        if (!destination.rootOffset && TEq(destination.root->type, destination.place.type)) {
            StoreAddress(destination.place); code.I32(0); code.Mem(0x3a, 0, destination.place.offset);
        }
        return;
    }
    auto dest = Local(WasmModule::I64), src = Local(WasmModule::I64), length = Local(WasmModule::I32);
    EmitPackedAddress(destination.place, line); code.Set(dest);
    EmitPackedAddress(source, line); code.Set(src);
    code.I32((int32_t)destination.image); code.Set(length);
    CopyBytes({destination.place.type, dest, 0, destination.place.memory, true, true},
              {source.type, src, 0, source.memory, true, source.bounded}, length, line);
}

inline void WasmCodeGen::ConstructFixed(FreshFixedDestination fresh, Node *source) {
    auto destination = fresh.place;
    if (destination.memory != 0 || !destination.bounded)
        Fail(source->line, "fixed construction needs a fresh planned destination");
    auto type = destination.type;
    if (type->kind == TY_ARRAY && !InlineArray(type))
        Fail(source->line, "nonfixed fields need the pending destination lowering");
    auto bytes = RequireFixed(type, source->line);
    if (bytes != fresh.image) Fail(source->line, "fixed construction has an inconsistent image");
    auto zero = [&](uint32_t count) {
        if (!count) return;
        PlaceAddress(destination, WasmModule::I32, source->line);
        code.I32(0); code.I32((int32_t)count); code.Fill(0);
    };
    while (auto call = Is<Call>(source)) {
        if (call->builtin == B_COPY) { source = call->ValueArgNodes().at(0); continue; }
        if (call->builtin != B_DEFAULT) break;
        if (Nominal(type) && call->defaultinit) { source = call->defaultinit; continue; }
        if (InlineArray(type)) {
            if (Nominal(type->arr->sub))
                Fail(source->line, "aggregate array defaults need the pending destination lowering");
            if (type->arr->akind == A_FIXED) zero(bytes);
            else {
                auto place = ArrayFromPlace(destination, source->line);
                PrepareArrayLengthStore(place); code.I64(0); StoreArrayLength(place);
            }
            return;
        }
        Fail(source->line, "this default needs the pending destination lowering");
    }
    auto tag = [&](EnumInst *instance, int variant) {
        auto field = destination;
        field.type = ast.inttypes[TagStore(instance->en)];
        StoreAddress(field); code.I64(variant); StorePlace(field);
    };
    if (Nominal(type)) if (auto literal = Is<StructLit>(source)) {
        if (type->kind == TY_STRUCT) {
            auto si = SI(type);
            if (literal->sinst != si)
                Fail(source->line, "aggregate adaptation needs the pending destination lowering");
            if (LastRealField(si->st->fields) < 0) { zero(bytes); return; }
            ConstructFields(fresh, literal, FieldsOf(type, source->line), 0, source->line);
        } else {
            auto ei = type->kind == TY_ENUM ? EIOf(type) : EIVar(type);
            if (literal->einst != ei || !literal->variant ||
                (type->kind == TY_VARIANT && literal->variant != type->var->variant))
                Fail(source->line, "aggregate adaptation needs the pending destination lowering");
            auto vi = ei->en->VariantIndex(literal->variant);
            auto view = VariantFields(ei, vi, source->line);
            auto prefix = type->kind == TY_ENUM ? (uint32_t)TagSize(ei->en) : 0u;
            if (type->kind == TY_ENUM) tag(ei, vi);
            if (LastRealField(view.fields) < 0) {
                if (!prefix && (bytes || (!fresh.rootOffset && TEq(fresh.root->type, type))))
                    zero(std::max(1u, bytes));
            } else ConstructFields(fresh, literal, view, prefix, source->line);
        }
        return;
    }
    if (type->kind == TY_ENUM) if (auto constant = Is<Dot>(source); constant && constant->variantconst) {
        auto ei = EIOf(type);
        if (constant->einst != ei) Fail(source->line, "aggregate adaptation needs the pending destination lowering");
        auto vi = ei->en->VariantIndex(constant->variantconst);
        auto view = VariantFields(ei, vi, source->line);
        if (view.layout.size) Fail(source->line, "variant constant has a nonempty payload");
        tag(ei, vi); return;
    }
    if (InlineArray(type)) {
        if (auto text = Is<StrLit>(source)) { InitByteString(nullptr, nullptr, text, &destination); return; }
        if (auto literal = Is<ArrayLit>(source)) {
            if (Nominal(type->arr->sub)) { ConstructAggregateArray(fresh, literal); return; }
            if (literal->capexpr) Fail(source->line, "this capacity constructor needs the pending destination lowering");
            if (literal->fillval) { InitFilledArray(nullptr, nullptr, literal, &destination); return; }
            auto header = Local(WasmModule::I32);
            PlaceAddress(destination, WasmModule::I32, source->line); code.Set(header);
            InlineArrayLiteral(ArrayFromPlace({type, header, 0, 0, false, true}, source->line), literal, true); return;
        }
    }
    auto from = ActualType(source);
    while (from && from->kind == TY_REF) from = from->ref->sub;
    if (!from || !TEq(type, from)) Fail(source->line, "aggregate adaptation needs the pending destination lowering");
    CopyFixed(fresh, ResolvePlace(source), source->line);
}

inline void WasmCodeGen::EnumMatchStatement(MatchExpr *match) {
    if (!Void(match->exprtype)) Fail(match->line, "value-producing matches need the pending destination lowering");
    auto source = ResolvePlace(match->scrutinee);
    if (source.type->kind != TY_ENUM)
        Fail(match->line, "this match needs the pending destination lowering");
    auto image = RequireFixed(source.type, match->line);
    auto ei = EIOf(source.type);
    auto prefix = (uint32_t)TagSize(ei->en);
    auto tag = source; tag.type = ast.inttypes[TagStore(ei->en)];
    auto captured = Local(WasmModule::I64);
    ReadPlace(tag); code.Set(captured);
    code.Get(captured); code.I64((int64_t)ei->en->variants.size()); code.Byte(0x5a);
    Open(0x04); Trap(14, match->line); Close();
    auto done = Open();
    for (auto &arm : match->arms) {
        auto conditional = arm.pat.kind != P_WILDCARD;
        if (conditional) {
            if (arm.variants.empty()) Fail(match->line, "missing checked enum arm");
            for (size_t i = 0; i < arm.variants.size(); i++) {
                code.Get(captured); code.I64(ei->en->VariantIndex(arm.variants[i])); code.Byte(0x51);
                if (i) code.Byte(0x72);
            }
            Open(0x04);
        }
        scopes.emplace_back();
        if (arm.binder) {
            if (arm.pat.byref || arm.variants.size() != 1 || arm.binder->type->kind != TY_VARIANT)
                Fail(match->line, "reference payload bindings need the pending destination lowering");
            auto type = arm.binder->type;
            if (EIVar(type) != ei || type->var->variant != arm.variants[0])
                Fail(match->line, "payload binding has an inconsistent variant");
            auto payload = RequireFixed(type, match->line);
            if (prefix > image || payload > image - prefix || prefix > UINT32_MAX - source.offset)
                Fail(match->line, "payload exceeds its fixed enum image");
            auto selected = source; selected.offset += prefix; selected.type = type;
            CopyFixed(FreshOwner(arm.binder, match), selected, match->line);
        }
        Statement(arm.body);
        Cleanup(scopes.size() - 1); scopes.pop_back(); Branch(done);
        if (conditional) Close();
        else break;
    }
    Close();
}

inline bool WasmCodeGen::FieldPath(Node *n) {
    if (auto field = Is<Dot>(n)) return field->IsField();
    if (auto index = Is<Index>(n)) return FieldPath(index->obj);
    if (auto address = Is<Unary>(n); address && address->op == T_BITAND) return FieldPath(address->child);
    return false;
}

}  // namespace goose
