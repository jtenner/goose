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
    if (Nominal(owner->type) || storage.fixedvalues.count(owner)) {
        auto it = storage.fixedvalues.find(owner);
        auto declaration = Is<VarDecl>(initialization);
        auto argument = declaration && declaration->inline_arg;
        if (it == storage.fixedvalues.end() || it->second.initialization != initialization ||
            it->second.argument != argument || !it->second.initialized || it->second.image != image)
            Fail(owner->line, "fixed construction needs its planned fresh owner");
    } else {
        auto declaration = Is<VarDecl>(initialization);
        if (!InlineArray(owner->type) || !declaration || declaration->inline_arg ||
            find(declaration->defs.begin(), declaration->defs.end(), owner) == declaration->defs.end())
            Fail(owner->line, "fixed construction needs its planned fresh owner");
    }
    return {OwnerPlace(owner), owner, 0, image, FreshFixedOrigin::PlannedFrame,
            initialization, std::max(1u, image)};
}

inline WasmCodeGen::FreshFixedDestination WasmCodeGen::FreshCallParameter(Call *call, size_t position) {
    if (!call->fvbody || position >= call->fvparams.size())
        Fail(call->line, "aggregate callback parameter needs its checked call index");
    auto owner = call->fvparams[position];
    auto plan = storage.fixedvalues.find(owner);
    auto image = RequireFixed(owner->type, call->line);
    if (!FixedParameter(owner->type) || !image ||
        plan == storage.fixedvalues.end() ||
        plan->second.origin != WasmStoragePlan::FixedOrigin::CallbackParameter ||
        plan->second.function != current || plan->second.initialization != call ||
        !plan->second.argument || !plan->second.initialized || plan->second.image != image)
        Fail(call->line, "aggregate callback parameter needs its planned call owner");
    return {OwnerPlace(owner), owner, 0, image, FreshFixedOrigin::PlannedFrame, call,
            std::max(1u, image)};
}

inline TypeExpr *WasmCodeGen::FreshRootType(const FreshFixedDestination &destination) {
    if (destination.origin == FreshFixedOrigin::IncomingResult)
        return current && current->rets.size() == 1 ? current->rets[0] : nullptr;
    if (destination.origin == FreshFixedOrigin::ReservedFrameTemporary)
        return destination.temporary ? destination.temporary->type : nullptr;
    return destination.root ? destination.root->type : nullptr;
}

inline bool WasmCodeGen::IsFreshWholeOwner(const FreshFixedDestination &destination) {
    auto root = FreshRootType(destination);
    return root && !destination.rootOffset && TEq(root, destination.place.type);
}

inline void WasmCodeGen::CheckFreshDestination(const FreshFixedDestination &fresh, Line line) {
    auto &place = fresh.place;
    if (!fresh.initialization || !place.bounded || fresh.rootOffset > fresh.ownerBytes ||
        fresh.image > fresh.ownerBytes - fresh.rootOffset || RequireFixed(place.type, line) != fresh.image)
        Fail(line, "fixed construction needs its complete fresh owner span");
    if (fresh.origin == FreshFixedOrigin::IncomingResult) {
        if (!current || current->rets.size() != 1 || !FixedResult(current->rets[0]) ||
            fresh.root || fresh.temporary || fresh.initialization != current->body ||
            fresh.ownerBytes != std::max(1u, RequireFixed(current->rets[0], line)) ||
            place.memory != 0 || place.packed || place.address != FixedResultParameter(current) ||
            place.offset != fresh.rootOffset)
            Fail(line, "fixed result needs its checked incoming destination span");
    } else if (fresh.origin == FreshFixedOrigin::ReservedFrameTemporary) {
        auto owner = fresh.temporary;
        if (!owner || fresh.root || !owner->type || owner->scope >= scopes.size() ||
            owner->expression != fresh.initialization || owner->bytes != fresh.ownerBytes ||
            owner->image != RequireFixed(owner->type, line) || owner->bytes != std::max(1u, owner->image) ||
            place.memory != 0 || place.packed || place.address != owner->baseLocal ||
            place.offset != fresh.rootOffset)
            Fail(line, "fixed temporary needs its active checked frame owner");
        auto &actions = scopes[owner->scope];
        if (none_of(actions.begin(), actions.end(), [&](const CleanupAction &action) {
                return !action.deferred && action.snapshot == UINT32_MAX && !action.dynamic &&
                       action.memory == 0 && action.top == owner->baseLocal;
            })) Fail(line, "fixed temporary is missing its ordered frame restore");
    } else {
        if (!fresh.root || fresh.temporary ||
            (fresh.origin == FreshFixedOrigin::PlannedFrame && place.memory != 0) ||
            (fresh.origin == FreshFixedOrigin::ReservedDataElement &&
             (!support.DataNominalArray(fresh.root->type) || !place.packed)))
            Fail(line, "fixed construction needs a fresh planned destination");
    }
}

template<class Consume>
inline void WasmCodeGen::WithFixedTemporary(TypeExpr *type, Node *expression, Consume consume) {
    assert(expression);
    if (!Nominal(type) && !InlineArray(type))
        Fail(expression->line, "fixed temporary needs a fixed stored value");
    auto image = RequireFixed(type, expression->line);
    auto bytes = std::max(1u, image);
    auto scope = scopes.size(); scopes.emplace_back();
    auto base = Local(WasmModule::I32);
    code.I32((int32_t)bytes); code.Call(reservefn); code.Set(base);
    // reservefn returns the old top, also the base of this complete reservation.
    scopes.back().push_back({nullptr, 0, base, false});
    FixedTemporaryOwner owner {type, expression, base, image, bytes, scope};
    FreshFixedDestination fresh {{type, base, 0, 0, false, true}, nullptr, 0, image,
                                 FreshFixedOrigin::ReservedFrameTemporary, expression, bytes, &owner};
    ConstructFixed(fresh, expression);
    consume(fresh.place);
    Cleanup(scope); scopes.pop_back();
}

inline void WasmCodeGen::FixedCallArguments(Call *call, const vector<Node *> &arguments,
                                           vector<uint32_t> &values, size_t position, uint32_t result,
                                           uint32_t destination) {
    if (position == arguments.size()) {
        for (auto value : values) code.Get(value);
        if (NeedsBase(call->spec)) StackIndex((uint32_t)storage.calltops.at(call));
        if (destination != NoLocal) code.Get(destination);
        code.Call(functions.at(call->spec));
        if (result != NoLocal) code.Set(result);
        return;
    }
    auto expression = arguments[position];
    if (ExitingFixedInitializer(expression)) return;
    auto type = call->spec->params[position]->type;
    if (FixedParameter(type)) {
        WithFixedTemporary(type, expression, [&](const FixedPlace &value) {
            values[position] = value.address;
            FixedCallArguments(call, arguments, values, position + 1, result, destination);
        });
    } else {
        Gen(expression); Convert(expression->exprtype, type);
        values[position] = Temp(type); code.Set(values[position]);
        FixedCallArguments(call, arguments, values, position + 1, result, destination);
    }
}

inline uint32_t WasmCodeGen::FixedResultParameter(FnSpec *function) {
    if (!function || function->rets.size() != 1 || !FixedResult(function->rets[0]))
        Fail(function ? function->sf->line : Line {}, "fixed result needs its checked function signature");
    return (uint32_t)function->params.size() + (NeedsBase(function) ? 1u : 0u);
}

inline void WasmCodeGen::BindCallParameters(Call *call) {
    for (auto parameter : call->fvparams) RequireCallValue(parameter->type, false, call->line);
    for (auto type : call->rettypes) RequireCallValue(type, true, call->line);
    auto arguments = call->ValueArgNodes();
    if (arguments.size() != call->fvparams.size()) Fail(call->line, "function-value parameter mismatch");
    for (size_t i = 0; i < arguments.size(); i++) {
        auto parameter = call->fvparams[i];
        if (FixedParameter(parameter->type)) ConstructFixed(FreshCallParameter(call, i), arguments[i]);
        else {
            Gen(arguments[i]); Convert(arguments[i]->exprtype, parameter->type); Write(Find(parameter));
        }
    }
}

inline void WasmCodeGen::BlockInto(Block *body, FreshFixedDestination destination) {
    CheckFreshDestination(destination, body->line);
    scopes.emplace_back();
    for (auto statement : body->stmts) Statement(statement);
    if (body->tail) ConstructFixed(destination, body->tail);
    Cleanup(scopes.size() - 1);
    scopes.pop_back();
}

inline void WasmCodeGen::CallInto(FreshFixedDestination destination, Node *expression) {
    CheckFreshDestination(destination, expression->line);
    auto type = ActualType(expression);
    if (!FixedResult(type) || !TEq(type, destination.place.type))
        Fail(expression->line, "aggregate result adaptation needs the pending destination lowering");
    RequireCallValue(type, true, expression->line);
    if (destination.place.memory != 0 || destination.place.packed) {
        WithFixedTemporary(type, expression, [&](const FixedPlace &value) {
            CopyFixed(destination, value, expression->line);
        });
        return;
    }
    if (auto inlined = Is<InlineBlock>(expression)) {
        for (auto parameter : inlined->spec->params) RequireCallValue(parameter->type, false, expression->line);
        for (auto result : inlined->spec->rets) RequireCallValue(result, true, expression->line);
        auto end = Open();
        targets.push_back({Target::Inline, inlined->sf, scopes.size(), end, -1, -1, type, &destination});
        BlockInto(inlined->body, destination);
        targets.pop_back(); Close(); return;
    }
    auto call = Is<Call>(expression);
    if (!call || call->builtin >= 0)
        Fail(expression->line, "aggregate result needs its checked call producer");
    if (call->fvbody) {
        BindCallParameters(call);
        BlockInto(call->fvbody, destination); return;
    }
    if (!call->dispatch.empty()) Fail(call->line, "ADT dispatch is not implemented");
    if (!call->spec || !functions.count(call->spec)) Fail(call->line, "missing direct function specialization");
    auto arguments = call->ValueArgNodes();
    if (arguments.size() != call->spec->params.size()) Fail(call->line, "call parameter mismatch");
    auto address = Local(WasmModule::I32);
    PlaceAddress(destination.place, WasmModule::I32, call->line); code.Set(address);
    vector<uint32_t> values(arguments.size(), NoLocal);
    FixedCallArguments(call, arguments, values, 0, NoLocal, address);
}

inline WasmCodeGen::FreshFixedDestination WasmCodeGen::FreshDataElement(
        const FreshDataArrayDestination &destination, uint32_t ordinal, Line line) {
    if (destination.literalCount == NoLocal || ordinal >= destination.literalCount ||
        !destination.initialization || !destination.ownerBytes)
        Fail(line, "data element needs its complete fresh literal reservation");
    auto offset = (uint64_t)destination.prefixBytes + (uint64_t)ordinal * destination.stride;
    if (offset > destination.ownerBytes || destination.stride > destination.ownerBytes - offset)
        Fail(line, "data element exceeds its fresh owner reservation");
    auto place = destination.image.image;
    place.type = destination.image.layout.element;
    place.offset = (uint32_t)offset;
    return {place, destination.root, (uint32_t)offset, destination.stride,
            FreshFixedOrigin::ReservedDataElement, destination.initialization, destination.ownerBytes};
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

inline WasmCodeGen::ArrayPlace WasmCodeGen::FreshArrayPlace(
        const FreshFixedDestination &destination, Line line) {
    CheckFreshDestination(destination, line);
    auto place = ArrayFromPlace(destination.place, line);
    if (destination.origin == FreshFixedOrigin::ReservedDataElement) {
        if (!destination.root || !destination.initialization || !destination.place.bounded || !destination.place.packed ||
            !support.DataNominalArray(destination.root->type) ||
            destination.rootOffset > destination.ownerBytes ||
            destination.image > destination.ownerBytes - destination.rootOffset)
            Fail(line, "array construction needs its complete fresh data span");
        place.origin = ArrayOrigin::FreshDataElement;
    }
    return place;
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
    return FieldPlace(field, ResolvePlace(field->obj));
}

inline WasmCodeGen::FixedPlace WasmCodeGen::FieldPlace(Dot *field, FixedPlace object) {
    while (object.type->kind == TY_REF) object = DereferencePlace(object, field->line);
    auto [type, offset] = StoredField(object.type, field->fieldidx, field->line);
    if (field->accessorowner && !TEq(field->accessorowner, object.type))
        Fail(field->line, "field adaptation needs the pending layout lowering");
    if ((uint64_t)offset > UINT32_MAX - object.offset) Fail(field->line, "field offset exceeds memory32");
    object.offset += (uint32_t)offset; object.type = type;
    return object;
}

inline bool WasmCodeGen::HasFixedTemporary(Node *n) {
    if (auto field = Is<Dot>(n); field && field->IsField()) return HasFixedTemporary(field->obj);
    if (auto index = Is<Index>(n)) return HasFixedTemporary(index->obj);
    auto call = Is<Call>(n);
    auto variant = Is<Dot>(n);
    auto unary = Is<Unary>(n);
    auto producer = (call && (call->builtin < 0 || call->builtin == B_DEFAULT || call->builtin == B_COPY)) ||
                    (unary && unary->op == T_MINUS) ||
                    Is<InlineBlock>(n) || Is<StructLit>(n) || Is<ArrayLit>(n) || Is<Block>(n) || Is<IfExpr>(n) ||
                    (variant && variant->variantconst);
    return producer && FixedResult(ActualType(n));
}

template<class Consume>
inline void WasmCodeGen::WithReadPlace(Node *n, Consume consume) {
    WithReadPlace(n, &consume, [](void *context, const FixedPlace &place) {
        (*static_cast<Consume *>(context))(place);
    });
}

inline void WasmCodeGen::WithReadPlace(Node *n, void *context, FixedReadConsumer consume) {
    // The contexts live on the compiler stack. Recursion uses one callback
    // type, without allocating a std::function or recursively expanding lambda types.
    if (auto field = Is<Dot>(n); field && field->IsField()) {
        struct Step { WasmCodeGen *gen; Dot *field; void *context; FixedReadConsumer consume; };
        Step step {this, field, context, consume};
        WithReadPlace(field->obj, &step, [](void *context, const FixedPlace &object) {
            auto &step = *static_cast<Step *>(context);
            auto place = step.gen->FieldPlace(step.field, object);
            step.consume(step.context, place);
        });
        return;
    }
    if (auto index = Is<Index>(n)) {
        struct Step { WasmCodeGen *gen; Index *index; void *context; FixedReadConsumer consume; };
        Step step {this, index, context, consume};
        WithReadPlace(index->obj, &step, [](void *context, const FixedPlace &object) {
            auto &step = *static_cast<Step *>(context);
            auto place = object;
            while (place.type->kind == TY_REF) place = step.gen->DereferencePlace(place, step.index->line);
            if (!step.gen->TEq(place.type, step.gen->ArrayType(step.index->obj)))
                step.gen->Fail(step.index->line, "temporary array adaptation needs the pending layout lowering");
            auto array = step.gen->ArrayFromPlace(place, step.index->line);
            auto element = step.gen->ElementAddress(step.index, array);
            auto selected = step.gen->CaptureElementPlace(element);
            step.consume(step.context, selected);
        });
        return;
    }
    if (HasFixedTemporary(n)) {
        WithFixedTemporary(ActualType(n), n, [&](const FixedPlace &place) { consume(context, place); });
        return;
    }
    auto place = ResolvePlace(n);
    consume(context, place);
}

inline bool WasmCodeGen::ReadFixedTemporary(Node *n, TypeExpr *resulttype) {
    auto field = Is<Dot>(n);
    auto length = field && (field->member == B_LEN || field->member == B_CAP);
    if (!Is<Index>(n) && !(field && (field->IsField() || length))) return false;
    auto source = length ? field->obj : n;
    auto wanted = resulttype ? resulttype : n->exprtype;
    if (Aggregate(wanted) || !HasFixedTemporary(source)) return false;
    auto actual = ActualType(n);
    if (!length && wanted->kind == TY_REF && TEq(wanted->ref->sub, actual))
        Fail(n->line, "references into fixed temporaries need the pending lifetime lowering");
    auto value = Temp(wanted);
    WithReadPlace(source, [&](const FixedPlace &selected) {
        if (length) {
            auto place = selected;
            while (place.type->kind == TY_REF) place = DereferencePlace(place, n->line);
            auto array = ArrayFromPlace(place, n->line);
            if (field->member == B_LEN) ArrayLength(array);
            else if (VariableArray(array.layout.type)) Fail(n->line, "variable arrays have no static capacity");
            else ArrayCapacity(array);
        } else {
            ReadPlace(selected); Convert(selected.type, wanted);
        }
        code.Set(value);
    });
    code.Get(value);
    return true;
}

inline void WasmCodeGen::AssignFixed(FixedPlace destination, Node *source, TType op, Line line) {
    auto array = InlineArray(destination.type);
    auto fail = [&](const char *reason) {
        Fail(line, cat(array ? "whole-array assignment " : "whole-aggregate assignment ", reason));
    };
    if (op != T_ASSIGN || !source || (!Nominal(destination.type) && !array))
        fail("needs an exact fixed value");
    while (auto call = Is<Call>(source)) {
        if (call->builtin != B_COPY) break;
        source = call->ValueArgNodes().at(0);
    }
    auto from = ActualType(source);
    while (from && from->kind == TY_REF) from = from->ref->sub;
    if (!from || !TEq(destination.type, from))
        fail("adaptation needs the pending destination lowering");
    auto dot = Is<Dot>(source);
    auto call = Is<Call>(source);
    if (Is<StructLit>(source) || (dot && dot->variantconst) || (call && call->builtin == B_DEFAULT) ||
        (array && Is<ArrayLit>(source)) ||
        (Is<Unary>(source) && Is<Unary>(source)->op == T_MINUS && FixedResult(ActualType(source))) ||
        (Is<Block>(source) || Is<IfExpr>(source)) ||
        (((call && call->builtin < 0) || Is<InlineBlock>(source)) && FixedResult(ActualType(source)))) {
        WithFixedTemporary(destination.type, source, [&](const FixedPlace &value) {
            CopyBytes(destination, value, RequireFixed(destination.type, line), line, true);
        });
        return;
    }
    auto addressable = Is<Ident>(source) || (dot && dot->IsField()) || Is<Index>(source) ||
                       (Is<Unary>(source) && Is<Unary>(source)->op == T_BITAND) ||
                       ((Is<Call>(source) || Is<InlineBlock>(source)) && ActualType(source)->kind == TY_REF);
    if (!addressable)
        fail("from a temporary needs the pending destination lowering");
    auto copy = [&](FixedPlace selected) {
        while (selected.type->kind == TY_REF) selected = DereferencePlace(selected, line);
        if (!TEq(destination.type, selected.type)) fail("has an inconsistent source layout");
        CopyBytes(destination, selected, RequireFixed(destination.type, line), line, true);
    };
    if (HasFixedTemporary(source)) WithReadPlace(source, copy);
    else copy(ResolvePlace(source));
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
    if (Nominal(place.type) || InlineArray(place.type)) { AssignFixed(place, rhs, op, line); return; }
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
            auto value = literal->elems[i];
            if (ExitingFixedInitializer(value)) return;
            if (place.image.memory >= 0) {
                EmitKnownOffset(place.image, (uint32_t)place.image.memory, literal->line);
                code.I32((int32_t)(i * place.layout.stride)); code.Byte(0x6a);
            } else {
                EmitPackedAddress(place.image, literal->line);
                code.I64((int64_t)(i * place.layout.stride)); code.Byte(0x7c);
            }
            Gen(value); Convert(value->exprtype, element);
            if (place.elementMemory >= 0) StoreFixed(element, (uint32_t)place.elementMemory);
            else Store(element);
        }
    } else {
        PrepareArrayLengthStore(place); code.I64(0); StoreArrayLength(place);
        PushScratch *scratch = nullptr;
        if (reuse && !literal->elems.empty()) {
            if (place.layout.image != ArrayImage::Inline)
                Fail(literal->line, "fixed constructor scratch requires an inline image");
            auto &cached = fixedpushscratch[WasmModule::I32 - Type(array->arr->sub)];
            if (!cached)
                cached = PushScratch {Temp(array->arr->sub), Local(WasmModule::I64), NoLocal,
                                      Local(WasmModule::I64), Local(WasmModule::I64),
                                      Local(WasmModule::I64)};
            scratch = &*cached;
        }
        for (auto value : literal->elems) {
            if (ExitingFixedInitializer(value)) return;
            PushArray(place, value, nullptr, value->line, scratch);
        }
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
        // The checker drops the value tail when an initializer always exits.
        // No later field or destination store is reachable on this path.
        if (init && ExitingFixedInitializer(init)) return;
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

inline void WasmCodeGen::ConstructRepeatedAggregate(FreshFixedDestination destination, Node *value,
                                                     uint64_t count, bool each) {
    auto line = destination.initialization->line;
    CheckFreshDestination(destination, line);
    auto array = destination.place.type;
    if (!InlineArray(array) || !Nominal(array->arr->sub))
        Fail(line, "repeated aggregate construction needs a fixed array destination");
    auto element = array->arr->sub;
    auto stride = RequireFixed(element, line);
    if (!stride) Fail(line, "zero-stride aggregate elements need the pending layout lowering");
    auto capacity = (uint64_t)ArrSize(array->arr);
    auto prefix = array->arr->akind == A_LIMITED ? (uint32_t)IntSize(LenStore(array->arr)) : 0u;
    if (count > capacity || (array->arr->akind == A_FIXED && count != capacity) ||
        prefix > destination.image || count > (destination.image - prefix) / stride)
        Fail(line, "aggregate fill exceeds its checked array extent");
    if (prefix) InitArrayCount(FreshArrayPlace(destination, line), count);
    if (each && !count) return;
    if (!value) Fail(line, "aggregate construction needs its checked element initializer");
    auto base = Local(WasmModule::I64), position = Local(WasmModule::I64);
    auto address = Local(WasmModule::I64);
    EmitPackedAddress(destination.place, line); code.Set(base);
    auto copy = [&](const FixedPlace &item) {
        code.Get(base); code.Get(position); code.I64(stride); code.Byte(0x7e); code.Byte(0x7c);
        if (prefix) { code.I64(prefix); code.Byte(0x7c); }
        code.Set(address);
        // The complete fresh owner and count bound prove this element span.
        CopyBytes({element, address, 0, destination.place.memory, true, true},
                  item, stride, line, true);
    };
    auto loop = [&](auto body) {
        code.I64(0); code.Set(position);
        auto done = Open(), head = Open(0x03);
        code.Get(position); code.I64((int64_t)count); code.Byte(0x5a); Branch(done, true);
        body();
        code.Get(position); code.I64(1); code.Byte(0x7c); code.Set(position);
        Branch(head); Close(); Close();
    };
    if (each) {
        loop([&] { WithFixedTemporary(element, value, copy); });
    } else {
        // Even an empty fill evaluates and captures its value once.
        WithFixedTemporary(element, value, [&](const FixedPlace &item) {
            if (count) loop([&] { copy(item); });
        });
    }
}

inline void WasmCodeGen::ConstructAggregateArray(FreshFixedDestination destination, ArrayLit *literal) {
    auto array = destination.place.type;
    if (!InlineArray(array) || !Nominal(array->arr->sub))
        Fail(literal->line, "aggregate array construction needs a fixed Memory 0 destination");
    if (literal->fillval) {
        auto count = Is<IntLit>(literal->fillcount);
        if (!count || count->val < 0)
            Fail(literal->line, "array fill needs a nonnegative constant count");
        ConstructRepeatedAggregate(destination, literal->fillval, (uint64_t)count->val, false);
        return;
    }
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
        auto place = FreshArrayPlace(destination, literal->line);
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
            CopyBytes(child.place, {element, source.global ? NoLocal : framebase,
                                   source.offset, 0, false, true},
                      stride, init->line, true);
        } else ConstructFixed(child, init);
    }
}

inline void WasmCodeGen::CopyFixed(FreshFixedDestination destination, FixedPlace source, Line line) {
    CheckFreshDestination(destination, line);
    if (!TEq(destination.place.type, source.type))
        Fail(line, "aggregate adaptation needs the pending destination lowering");
    if (!destination.image) {
        // An empty standalone owner has an identity byte, but no payload image.
        if (IsFreshWholeOwner(destination)) {
            if (destination.place.memory >= 0) {
                StoreAddress(destination.place); code.I32(0);
                code.Mem(0x3a, (uint32_t)destination.place.memory, destination.place.offset);
            } else {
                EmitPackedAddress(destination.place, line); code.I32(0);
                code.Call(memories->Access(0x3a));
            }
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

inline bool WasmCodeGen::ExitingFixedInitializer(Node *source) {
    if (!Void(source->exprtype)) return false;
    Gen(source); code.Byte(0x00); return true;
}

// The caller owns a checked fresh complete destination. Array loop bounds
// and shared field offsets retain that image proof for every scalar leaf.
inline void WasmCodeGen::NegateFixedInto(FixedPlace destination, FixedPlace source, Line line) {
    auto type = destination.type;
    if (!TEq(type, source.type)) Fail(line, "fixed negation needs an exact source layout");
    if (!RequireFixed(type, line)) return;
    if (type->kind == TY_STRUCT) {
        auto fields = FieldsOf(type, line);
        for (size_t i = 0; i < fields.types.size(); i++) if (auto field = fields.types[i]) {
            auto offset = (uint64_t)fields.layout.offs[i];
            if (offset > UINT32_MAX - destination.offset || offset > UINT32_MAX - source.offset)
                Fail(line, "fixed negation field offset exceeds memory32");
            auto to = destination, from = source;
            to.type = from.type = field;
            to.offset += (uint32_t)offset; from.offset += (uint32_t)offset;
            NegateFixedInto(to, from, line);
        }
        return;
    }
    if (type->kind == TY_ARRAY) {
        if (type->arr->akind != A_FIXED)
            Fail(line, "fixed negation needs fixed-length array elements");
        auto count = ArrSize(type->arr);
        if (count < 0) Fail(line, "fixed negation needs a resolved array count");
        if (!count) return;
        auto to = ArrayFromPlace(destination, line), from = ArrayFromPlace(source, line);
        ArrayView toview {to}, fromview {from};
        auto position = Local(WasmModule::I64);
        code.I64(0); code.Set(position);
        auto done = Open(), head = Open(0x03);
        code.Get(position); code.I64(count); code.Byte(0x5a); Branch(done, true);
        ElementOffset(toview, position, line);
        auto element = CaptureElementPlace({type->arr->sub, to.elementMemory, true});
        ElementOffset(fromview, position, line);
        auto operand = CaptureElementPlace({type->arr->sub, from.elementMemory, true});
        NegateFixedInto(element, operand, line);
        code.Get(position); code.I64(1); code.Byte(0x7c); code.Set(position);
        Branch(head); Close(); Close();
        return;
    }
    if (type->kind == TY_INT) {
        if (IsUnsigned(type->intstorage) || type->intstorage == IS_VARINT || type->ix)
            Fail(line, "fixed negation needs ordinary signed integer leaves");
        StoreAddress(destination); code.I64(0); ReadPlace(source); code.Byte(0x7d); Normalize(type);
        StorePlace(destination);
        return;
    }
    if (type->kind == TY_FLT) {
        StoreAddress(destination); ReadPlace(source);
        code.Byte(type->fltstorage == FS_F32 ? 0x8c : 0x9a); StorePlace(destination);
        return;
    }
    Fail(line, "fixed negation needs numeric struct or fixed-array leaves");
}

inline void WasmCodeGen::ConstructFixed(FreshFixedDestination fresh, Node *source) {
    auto destination = fresh.place;
    CheckFreshDestination(fresh, source->line);
    if (ExitingFixedInitializer(source)) return;
    auto type = destination.type;
    if (type->kind == TY_ARRAY && !InlineArray(type))
        Fail(source->line, "nonfixed fields need the pending destination lowering");
    auto bytes = RequireFixed(type, source->line);
    if (bytes != fresh.image) Fail(source->line, "fixed construction has an inconsistent image");
    auto zero = [&](uint32_t count) {
        if (!count) return;
        ZeroFixed(destination, count, source->line);
    };
    while (auto call = Is<Call>(source)) {
        if (call->builtin == B_COPY) { source = call->ValueArgNodes().at(0); continue; }
        if (call->builtin != B_DEFAULT) break;
        if (Nominal(type) && call->defaultinit) { source = call->defaultinit; continue; }
        if (InlineArray(type)) {
            auto declared = ActualType(call);
            if (!declared || !InlineArray(declared) || !TEq(type->arr->sub, declared->arr->sub))
                Fail(source->line, "array default element adaptation needs the pending destination lowering");
            RequireFixed(declared, source->line);
            auto count = declared->arr->akind == A_FIXED ? (uint64_t)ArrSize(declared->arr) : 0;
            auto capacity = (uint64_t)ArrSize(type->arr);
            if (count > capacity || (type->arr->akind == A_FIXED && count != capacity))
                Fail(source->line, "array default does not fit its checked destination");
            if (Nominal(type->arr->sub)) {
                ConstructRepeatedAggregate(fresh, call->defaultinit, count, true); return;
            }
            if (!TEq(type, declared)) {
                // A default fixed source keeps its count when built into a
                // wider limited image; defaulting the target would lose it.
                zero(bytes);
                if (type->arr->akind == A_LIMITED)
                    InitArrayCount(FreshArrayPlace(fresh, source->line), count);
            } else if (type->arr->akind == A_FIXED) zero(bytes);
            else {
                auto place = FreshArrayPlace(fresh, source->line);
                PrepareArrayLengthStore(place); code.I64(0); StoreArrayLength(place);
            }
            return;
        }
        Fail(source->line, "this default needs the pending destination lowering");
    }
    if (auto unary = Is<Unary>(source); unary && unary->op == T_MINUS && FixedResult(ActualType(source))) {
        if (!TEq(type, ActualType(source)))
            Fail(source->line, "fixed negation adaptation needs the pending destination lowering");
        WithReadPlace(unary->child, [&](FixedPlace operand) {
            while (operand.type->kind == TY_REF) operand = DereferencePlace(operand, source->line);
            NegateFixedInto(destination, operand, source->line);
        });
        return;
    }
    auto resultCall = Is<Call>(source);
    if (((resultCall && resultCall->builtin < 0) || Is<InlineBlock>(source)) && FixedResult(ActualType(source))) {
        CallInto(fresh, source); return;
    }
    if (FixedResult(type)) {
        if (auto block = Is<Block>(source)) { BlockInto(block, fresh); return; }
        if (auto branch = Is<IfExpr>(source)) {
            if (!branch->elseb) Fail(source->line, "fixed conditional construction needs its checked else branch");
            Condition(branch->cond); Open(0x04);
            BlockInto(branch->thenb, fresh);
            code.Byte(0x05); ConstructFixed(fresh, branch->elseb);
            Close(); return;
        }
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
                if (!prefix && (bytes || IsFreshWholeOwner(fresh)))
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
        if (auto text = Is<StrLit>(source)) { InitByteString(nullptr, nullptr, text, &fresh); return; }
        if (auto literal = Is<ArrayLit>(source)) {
            if (Nominal(type->arr->sub)) { ConstructAggregateArray(fresh, literal); return; }
            if (literal->capexpr) Fail(source->line, "this capacity constructor needs the pending destination lowering");
            if (literal->fillval) { InitFilledArray(nullptr, nullptr, literal, &fresh); return; }
            InlineArrayLiteral(FreshArrayPlace(fresh, source->line), literal, true); return;
        }
    }
    auto from = ActualType(source);
    while (from && from->kind == TY_REF) from = from->ref->sub;
    if (!from || !TEq(type, from)) Fail(source->line, "aggregate adaptation needs the pending destination lowering");
    if (fresh.origin == FreshFixedOrigin::ReservedDataElement && Nominal(type)) {
        if (auto id = Is<Ident>(source); id && id->vdef && TEq(type, id->vdef->type)) {
            auto &slot = Find(id->vdef);
            if (!slot.memory) Fail(source->line, "fixed source owner is missing planned storage");
            FixedPlace named {type, slot.global ? NoLocal : framebase, slot.offset, 0, false, true};
            if (bytes) CopyBytes(destination, named, bytes, source->line, true);
            else CopyFixed(fresh, named, source->line);
            return;
        }
    }
    if (HasFixedTemporary(source)) {
        WithReadPlace(source, [&](FixedPlace selected) {
            while (selected.type->kind == TY_REF) selected = DereferencePlace(selected, source->line);
            CopyFixed(fresh, selected, source->line);
        });
    } else CopyFixed(fresh, ResolvePlace(source), source->line);
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
