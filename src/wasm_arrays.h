// Initial growable scalar-array lowering. Storage assignment is complete
// before these methods emit code; data memories are never chosen by type.
#pragma once

namespace goose {

inline TypeExpr *WasmCodeGen::ArrayType(Node *n) {
    auto t = n->exprtype;
    while (t && t->kind == TY_REF) t = t->ref->sub;
    if (!t || t->kind != TY_ARRAY || (!IsResz(t) && !InlineArray(t) && !DataArray(t)))
        Fail(n->line, "this array layout needs the pending compound lowering");
    Type(t);
    return t;
}

inline TypeExpr *WasmCodeGen::ArrayElement(Node *n) { return ArrayType(n)->arr->sub; }

inline WasmCodeGen::ArrayLayoutFacts WasmCodeGen::ArrayLayout(TypeExpr *array, Line line) {
    if (!array || array->kind != TY_ARRAY) Fail(line, "missing checked array layout");
    Type(array);
    auto growable = IsResz(array);
    return {array, array->arr->sub,
            growable ? ArrayImage::GrowableHeader : DataArray(array) ? ArrayImage::PrefixedData : ArrayImage::Inline,
            Size(array->arr->sub), ArrSize(array->arr),
            growable ? ArrayPrefixLayout {IS_U64, 8, 0} : ArrayPrefix(array->arr), VarintPrefix(array)};
}

inline WasmCodeGen::ArrayPlace WasmCodeGen::ArrayFromPlace(FixedPlace image, Line line) {
    auto layout = ArrayLayout(image.type, line);
    if (!image.packed && image.memory < 0) Fail(line, "array place is missing its memory proof");
    if (layout.image == ArrayImage::GrowableHeader && (image.memory != 0 || image.packed))
        Fail(line, "growable array headers require a Memory 0 place");
    return {image, layout, layout.image == ArrayImage::GrowableHeader ? -1 : image.memory,
            nullptr, ArrayOrigin::ParentPlace};
}

inline WasmCodeGen::ArrayPlace WasmCodeGen::ArrayOwner(VarDef *owner, FixedPlace image, Line line) {
    if (!TEq(owner->type, image.type)) Fail(line, "array owner has an inconsistent stored layout");
    auto place = ArrayFromPlace(image, line);
    place.owner = owner; place.origin = ArrayOrigin::PlannedOwner;
    if (place.layout.image == ArrayImage::GrowableHeader)
        place.elementMemory = storage.Memory(owner, current);
    return place;
}

inline WasmCodeGen::ArrayPlace WasmCodeGen::FrameArrayOwner(VarDef *owner, const Slot &slot, Line line) {
    if (!slot.memory || DataArray(slot.type)) Fail(line, "array header is missing its planned frame slot");
    auto place = ArrayOwner(owner, {slot.type, slot.global ? NoLocal : framebase, slot.offset, 0, false, true}, line);
    place.ownerSlot = &slot;
    return place;
}

inline int WasmCodeGen::ArrayAllocationMemory(VarDef *owner, const Slot *slot,
                                            const FixedPlace *destination, Line line) {
    if (destination) return destination->memory;
    if (owner && storage.owners.count(owner)) return storage.Memory(owner, current);
    if (!slot || !slot->memory) Fail(line, "array allocation is missing its storage plan");
    return 0; // The remaining allocation is the checked Memory 0 frame slot.
}

inline WasmCodeGen::ArrayPlace WasmCodeGen::CaptureArrayBorrow(
        TypeExpr *array, uint32_t value, uint8_t representation, ArrayOrigin origin, Line line) {
    // This bridge is the current scalar emitter's borrowed-array transport,
    // not an array-value ABI. Only the thin transport proves Memory 0.
    if (representation != BorrowedArrayAddressType(array))
        Fail(line, "incompatible borrowed array representation");
    auto packed = representation == WasmModule::I64;
    auto place = ArrayFromPlace({array, value, 0, packed ? -1 : 0, packed, false}, line);
    place.origin = origin;
    return place;
}

inline WasmCodeGen::ArrayPlace WasmCodeGen::RefineArrayOwner(ArrayPlace place, Node *n) {
    if (auto address = Is<Unary>(n); address && address->op == T_BITAND) n = address->child;
    auto id = Is<Ident>(n);
    if (id && id->vdef && id->vdef->type->kind == TY_ARRAY &&
        (InlineArray(id->vdef->type) || storage.owners.count(id->vdef))) {
        place.owner = id->vdef; place.origin = ArrayOrigin::PlannedOwner;
        place.elementMemory = storage.owners.count(id->vdef) ? storage.Memory(id->vdef, current) : 0;
        if (place.layout.image != ArrayImage::GrowableHeader) place.image.memory = place.elementMemory;
    }
    return place;
}

inline WasmCodeGen::ArrayPlace WasmCodeGen::ResolveArray(Node *n) {
    auto array = ArrayType(n);
    if (auto field = Is<Dot>(n); field && field->IsField()) {
        auto place = ResolvePlace(n);
        if (!TEq(place.type, array)) Fail(n->line, "array adaptation needs the pending destination lowering");
        PlaceAddress(place, BorrowedArrayAddressType(array), n->line);
        auto address = Local(BorrowedArrayAddressType(array)); code.Set(address);
        auto captured = CaptureArrayBorrow(array, address, BorrowedArrayAddressType(array),
                                           ArrayOrigin::ParentPlace, n->line);
        if (captured.layout.image != ArrayImage::GrowableHeader) {
            captured.image.memory = place.memory; captured.elementMemory = place.memory;
        }
        return captured;
    }
    Gen(n); Convert(n->exprtype, array);
    auto address = Local(BorrowedArrayAddressType(array)); code.Set(address);
    return RefineArrayOwner(CaptureArrayBorrow(array, address, BorrowedArrayAddressType(array),
                                              ArrayOrigin::ReferenceABI, n->line), n);
}

inline WasmCodeGen::ArrayPlace WasmCodeGen::ArrayFromReference(TypeExpr *reference, uint32_t value, Line line) {
    // The caller performed the existing null check before capturing this value.
    if (reference->kind != TY_REF || reference->ref->sub->kind != TY_ARRAY)
        Fail(line, "array reference is missing its checked pointee");
    return CaptureArrayBorrow(reference->ref->sub, value, Type(reference), ArrayOrigin::ReferenceABI, line);
}

inline void WasmCodeGen::EmitKnownOffset(const FixedPlace &place, uint32_t memory, Line line) {
    if (place.memory < 0 || (uint32_t)place.memory != memory)
        Fail(line, "array address is missing its concrete memory proof");
    if (place.address == NoLocal) { code.I32((int32_t)place.offset); return; }
    if (place.offset && !place.bounded) {
        EmitPackedAddress(place, line); code.Byte(0xa7); return;
    }
    code.Get(place.address);
    if (place.packed) code.Byte(0xa7);
    if (place.offset) { code.I32((int32_t)place.offset); code.Byte(0x6a); }
}

inline void WasmCodeGen::EmitPackedAddress(const FixedPlace &place, Line line) {
    if (!place.packed && place.memory < 0) Fail(line, "packed address is missing its memory proof");
    if (place.address == NoLocal) {
        if (place.memory < 0) Fail(line, "constant address is missing its memory proof");
        code.I64(((int64_t)place.memory << 32) | place.offset); return;
    }
    if (!place.packed && place.memory > 0 && !place.bounded) {
        auto offset = place; offset.memory = 0;
        PlaceAddress(offset, WasmModule::I64, line);
        code.I64((int64_t)place.memory << 32); code.Byte(0x84);
    } else PlaceAddress(place, WasmModule::I64, line);
}

inline void WasmCodeGen::EmitMemoryZeroReference(const FixedPlace &place, Line line) {
    if (place.address == NoLocal) {
        if (place.memory != 0) Fail(line, "this thin reference requires memory zero");
        code.I32((int32_t)place.offset); return;
    }
    PlaceAddress(place, WasmModule::I32, line);
}

inline void WasmCodeGen::EmitArrayReference(const ArrayPlace &place, TypeExpr *reference, Line line) {
    if (reference->kind != TY_REF || !TEq(reference->ref->sub, place.layout.type))
        Fail(line, "array reference has an inconsistent stored layout");
    if (Type(reference) == WasmModule::I32) EmitMemoryZeroReference(place.image, line);
    else EmitPackedAddress(place.image, line);
}

inline void WasmCodeGen::LoadArrayField(const ArrayPlace &place, uint32_t offset) {
    const auto &image = place.image;
    if (offset > UINT32_MAX - image.offset) Fail(image.type->line, "array field exceeds memory32");
    auto bytes = IntSize(place.layout.prefix.storage);
    auto opcode = (uint8_t)(bytes == 1 ? 0x31 : bytes == 2 ? 0x33 : bytes == 4 ? 0x35 : 0x29);
    if (place.ownerSlot) Address(*place.ownerSlot);
    else code.Get(image.address);
    auto displacement = place.ownerSlot ? offset : image.offset + offset;
    auto fresh = place.origin == ArrayOrigin::FreshDataElement;
    if (image.memory >= 0) {
        if (image.packed) code.Byte(0xa7);
        code.Mem(opcode, (uint32_t)image.memory, displacement);
    } else {
        // The full fresh child span proves this addition cannot carry into the memory id.
        if (fresh && displacement) { code.I64(displacement); code.Byte(0x7c); }
        code.Call(memories->Access(opcode, fresh ? 0 : displacement));
    }
}

inline void WasmCodeGen::PrepareArrayFieldStore(const ArrayPlace &place, uint32_t offset) {
    if (offset > UINT32_MAX - place.image.offset) Fail(place.layout.type->line, "array field exceeds memory32");
    if (place.ownerSlot) Address(*place.ownerSlot);
    else code.Get(place.image.address);
    if (place.origin == ArrayOrigin::FreshDataElement && place.image.memory < 0) {
        auto displacement = place.image.offset + offset;
        if (displacement) { code.I64(displacement); code.Byte(0x7c); }
    }
}

inline void WasmCodeGen::StoreArrayField(const ArrayPlace &place, uint32_t offset) {
    const auto &image = place.image;
    if (offset > UINT32_MAX - image.offset) Fail(image.type->line, "array field exceeds memory32");
    auto displacement = place.ownerSlot ? offset : image.offset + offset;
    auto bytes = IntSize(place.layout.prefix.storage);
    auto opcode = (uint8_t)(bytes == 1 ? 0x3c : bytes == 2 ? 0x3d : bytes == 4 ? 0x3e : 0x37);
    if (image.memory >= 0) {
        if (image.packed) {
            if (arraystorevalue == NoLocal) arraystorevalue = Local(WasmModule::I64);
            code.Set(arraystorevalue); code.Byte(0xa7); code.Get(arraystorevalue);
        }
        code.Mem(opcode, (uint32_t)image.memory, displacement);
    } else code.Call(memories->Access(opcode, place.origin == ArrayOrigin::FreshDataElement
                                             ? 0 : image.offset + offset));
}

inline void WasmCodeGen::ArrayLength(const ArrayPlace &place, int prefix) {
    if (place.layout.prefix.length < 0) { code.I64(place.layout.capacity); return; }
    if (place.layout.varint) {
        EmitPackedAddress(place.image, place.layout.type->line); code.Call(memories->ReadPrefix());
        if (prefix >= 0) code.Set((uint32_t)prefix);
        else code.Byte(0x1a);
        return;
    }
    LoadArrayField(place, (uint32_t)place.layout.prefix.length);
}

inline void WasmCodeGen::ArrayCapacity(const ArrayPlace &place) {
    if (RuntimeLimited(place.layout.type)) LoadArrayField(place, 0);
    else code.I64(place.layout.capacity);
}

inline void WasmCodeGen::PrepareArrayLengthStore(const ArrayPlace &place) {
    PrepareArrayFieldStore(place, (uint32_t)place.layout.prefix.length);
}

inline void WasmCodeGen::StoreArrayLength(const ArrayPlace &place) {
    StoreArrayField(place, (uint32_t)place.layout.prefix.length);
}

inline void WasmCodeGen::InitArrayCount(const ArrayPlace &place, uint64_t count) {
    if (place.layout.varint) {
        WasmBytes prefix; prefix.U(count);
        for (uint32_t i = 0; i < prefix.bytes.size(); i++) {
            code.Get(place.image.address);
            if (place.image.memory >= 0 && place.image.packed) code.Byte(0xa7);
            code.I64((uint8_t)prefix.bytes[i]);
            if (place.image.memory >= 0) code.Mem(0x3c, (uint32_t)place.image.memory, place.image.offset + i);
            else code.Call(memories->Access(0x3c, place.image.offset + i));
        }
        return;
    }
    if (RuntimeLimited(place.layout.type)) {
        PrepareArrayFieldStore(place, 0); code.I64((int64_t)count); StoreArrayField(place, 0);
    }
    PrepareArrayLengthStore(place); code.I64((int64_t)count); StoreArrayLength(place);
}

inline WasmCodeGen::ArrayView WasmCodeGen::CaptureArrayView(
        const ArrayPlace &place, uint32_t length, uint32_t prefix) {
    // Callers retain their existing local allocation and evaluation order.
    ArrayLength(place, prefix == NoLocal ? -1 : (int)prefix); code.Set(length);
    return {place, length, prefix};
}

inline void WasmCodeGen::ViewLength(const ArrayView &view) {
    if (view.length != NoLocal) code.Get(view.length);
    else ArrayLength(view.place, view.prefixBytes == NoLocal ? -1 : (int)view.prefixBytes);
}

inline void WasmCodeGen::CopyBytes(const FixedPlace &destination, const FixedPlace &source,
                                  uint32_t bytes, Line line, bool immediate) {
    auto count = [&]() { if (immediate) code.I32((int32_t)bytes); else code.Get(bytes); };
    if (destination.memory >= 0 && source.memory >= 0) {
        EmitKnownOffset(destination, (uint32_t)destination.memory, line);
        EmitKnownOffset(source, (uint32_t)source.memory, line); count();
        code.Copy((uint32_t)destination.memory, (uint32_t)source.memory);
    } else if (destination.memory == 0) {
        EmitKnownOffset(destination, 0, line); EmitPackedAddress(source, line); count();
        code.Call(memories->CopyToFrame());
    } else if (source.memory == 0) {
        EmitPackedAddress(destination, line); EmitKnownOffset(source, 0, line); count();
        code.Call(memories->CopyFromFrame());
    } else {
        EmitPackedAddress(destination, line); EmitPackedAddress(source, line); count();
        code.Call(memories->Copy());
    }
}

inline void WasmCodeGen::ZeroFixed(const FixedPlace &destination, uint32_t bytes, Line line) {
    if (!bytes) return;
    if (destination.memory >= 0) EmitKnownOffset(destination, (uint32_t)destination.memory, line);
    else EmitPackedAddress(destination, line);
    code.I32(0); code.I32((int32_t)bytes);
    if (destination.memory >= 0) code.Fill((uint32_t)destination.memory);
    else code.Call(memories->Fill());
}

inline void WasmCodeGen::InitArrayCopy(VarDef *owner, const Slot &slot, Node *source) {
    auto array = owner->type;
    // Check the storage type, not exprtype: the checker can adapt exprtype
    // to the destination while the source still has its original layout.
    auto from = ActualType(source);
    while (from && from->kind == TY_REF) from = from->ref->sub;
    if (!from || !TEq(array, from))
        Fail(source->line, "array adaptation needs the pending destination lowering");
    auto fromplace = ResolveArray(source);
    auto header = fromplace.image.address;
    auto sourceMemory = fromplace.elementMemory;
    auto bytes = Local(WasmModule::I32), sourceBase = Local(WasmModule::I64);
    int count = -1;
    if (InlineArray(array)) {
        code.I32((int32_t)Size(array)); code.Set(bytes);
        EmitPackedAddress(fromplace.image, source->line); code.Set(sourceBase);
    } else {
        auto prefix = DataArray(array) && !VarintPrefix(array) ? DataPrefix(array) : 0u;
        auto stride = Size(array->arr->sub);
        auto decodedPrefix = VarintPrefix(array) ? (int)Local(WasmModule::I32) : -1;
        count = (int)Local(WasmModule::I64);
        if (RuntimeLimited(array)) ArrayCapacity(fromplace);
        else ArrayLength(fromplace, decodedPrefix);
        code.Set(count);
        code.Get(count); code.I64((UINT32_MAX - prefix) / stride); code.Byte(0x56);
        Open(0x04); Trap(6, source->line); Close();
        code.Get(count); code.I64(stride); code.Byte(0x7e);
        if (decodedPrefix >= 0) {
            code.Get((uint32_t)decodedPrefix); code.Byte(0xad); code.Byte(0x7c);
            auto total = Local(WasmModule::I64); code.Tee(total);
            code.I64(UINT32_MAX); code.Byte(0x56);
            Open(0x04); Trap(6, source->line); Close();
            code.Get(total);
        } else if (prefix) { code.I64(prefix); code.Byte(0x7c); }
        code.Byte(0xa7); code.Set(bytes);
        code.Get(header);
        if (IsResz(array)) code.Mem(0x29);
        code.Set(sourceBase);
    }
    auto destination = Local(WasmModule::I64);
    auto memory = ArrayAllocationMemory(owner, &slot, nullptr, owner->line);
    if (InlineArray(array)) {
        Address(slot); code.Byte(0xad); code.Set(destination);
    } else {
        auto identity = Local(WasmModule::I32), saved = Local(WasmModule::I32);
        if (memory >= 0) code.I32(memory);
        else StackIndex(storage.owners.at(owner) + 1);
        code.Set(identity);
        if (memory < 0) code.Get(identity);
        code.Get(bytes); code.Call(memory >= 0 ? memories->Reserve((uint32_t)memory) : memories->ReserveDynamic());
        code.Set(saved);
        if (!owner->isglobal) {
            assert(!scopes.empty());
            scopes.back().push_back({nullptr, memory >= 0 ? (uint32_t)memory : identity, saved, memory < 0});
        }
        code.Get(identity); code.Byte(0xad); code.I64(32); code.Byte(0x86);
        code.Get(saved); code.Byte(0xad); code.Byte(0x84); code.Set(destination);
        if (DataArray(array)) { code.Get(destination); Write(slot); }
        else {
            Address(slot); code.Get(destination); code.Mem(0x37);
            Address(slot); code.Get(count); code.Mem(0x37, 0, 8);
        }
    }
    CopyBytes({array, destination, 0, memory, true, true},
              {from, sourceBase, 0, sourceMemory, true, true}, bytes, source->line);
}

inline void WasmCodeGen::InitLimitedCapacity(VarDef *owner, const Slot &slot, ArrayLit *literal) {
    auto array = owner->type;
    if (!RuntimeLimited(array)) Fail(literal->line, "runtime capacity needs a limited array");
    auto prefix = DataPrefix(array), stride = Size(array->arr->sub);
    auto capacity = Local(WasmModule::I64);
    Gen(literal->capexpr); code.Set(capacity);
    // The unsigned comparison rejects negative signed values as well.
    code.Get(capacity); code.I64(UINT32_MAX); code.Byte(0x56);
    Open(0x04); Trap(12, literal->line); Close();
    code.Get(capacity); code.I64((UINT32_MAX - prefix) / stride); code.Byte(0x56);
    Open(0x04); Trap(6, literal->line); Close();
    auto memory = storage.Memory(owner, current);
    auto identity = Local(WasmModule::I32), saved = Local(WasmModule::I32);
    if (memory >= 0) code.I32(memory);
    else StackIndex(storage.owners.at(owner) + 1);
    code.Set(identity);
    if (memory < 0) code.Get(identity);
    code.Get(capacity); code.I64(stride); code.Byte(0x7e); code.I64(prefix); code.Byte(0x7c); code.Byte(0xa7);
    code.Call(memory >= 0 ? memories->Reserve((uint32_t)memory) : memories->ReserveDynamic());
    code.Set(saved);
    if (!owner->isglobal) {
        assert(!scopes.empty());
        scopes.back().push_back({nullptr, memory >= 0 ? (uint32_t)memory : identity, saved, memory < 0});
    }
    auto header = Local(WasmModule::I64);
    code.Get(identity); code.Byte(0xad); code.I64(32); code.Byte(0x86);
    code.Get(saved); code.Byte(0xad); code.Byte(0x84); code.Set(header);
    code.Get(header); Write(slot);
    auto place = ArrayOwner(owner, {array, header, 0, memory, true, true}, literal->line);
    PrepareArrayFieldStore(place, 0); code.Get(capacity); StoreArrayField(place, 0);
    PrepareArrayLengthStore(place); code.I64(0); StoreArrayLength(place);
}

inline void WasmCodeGen::InitByteString(VarDef *owner, const Slot *slot, StrLit *literal,
                                       const FreshFixedDestination *fresh) {
    auto destination = fresh ? &fresh->place : nullptr;
    auto array = destination ? destination->type : owner->type;
    auto line = owner ? owner->line : literal->line;
    if (!ByteArray(array)) Fail(literal->line, "string literals require byte elements");
    auto count = literal->val.size();
    auto prefix = DataArray(array) ? DataPrefix(array, count) : 0u;
    if (count > UINT32_MAX - prefix) Fail(line, "array allocation exceeds memory32");
    if (prefix && prefix < 8 && count > ((1ull << (prefix * 8)) - 1))
        Fail(line, "array length exceeds its stored prefix");
    if (destination && InlineArray(array)) {
        auto capacity = (uint64_t)ArrSize(array->arr);
        if (count > capacity || (array->arr->akind == A_FIXED && count != capacity))
            Fail(line, "string literal does not fit its static layout");
        auto place = FreshArrayPlace(*fresh, literal->line);
        if (array->arr->akind == A_LIMITED) InitArrayCount(place, count);
        if (!count) return;
        auto payload = *destination;
        payload.type = array->arr->sub;
        payload.offset += array->arr->akind == A_LIMITED ? (uint32_t)IntSize(LenStore(array->arr)) : 0u;
        auto source = module.Data(literal->val);
        CopyBytes(payload, {array->arr->sub, NoLocal, (uint32_t)source, 0, false, true},
                  (uint32_t)count, literal->line, true);
        return;
    }
    auto memory = ArrayAllocationMemory(owner, slot, destination, line);
    auto base = Local(WasmModule::I64);
    if (InlineArray(array)) {
        auto packed = destination && (destination->packed || memory != 0);
        auto header = Local(packed ? WasmModule::I64 : WasmModule::I32);
        if (destination) PlaceAddress(*destination, packed ? WasmModule::I64 : WasmModule::I32, literal->line);
        else Address(*slot);
        code.Set(header);
        if (array->arr->akind == A_LIMITED) {
            auto place = ArrayFromPlace({array, header, 0, memory, packed, true}, literal->line);
            PrepareArrayLengthStore(place); code.I64((int64_t)count); StoreArrayLength(place);
        }
        code.Get(header);
        if (array->arr->akind == A_LIMITED) {
            if (packed) { code.I64(IntSize(LenStore(array->arr))); code.Byte(0x7c); }
            else { code.I32((int32_t)IntSize(LenStore(array->arr))); code.Byte(0x6a); }
        }
        if (!packed) code.Byte(0xad);
        code.Set(base);
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
        if (DataArray(array)) {
            code.Get(base); Write(*slot);
            InitArrayCount(ArrayOwner(owner, {array, base, 0, memory, true, true}, literal->line), count);
        } else {
            auto place = FrameArrayOwner(owner, *slot, literal->line);
            PrepareArrayFieldStore(place, 0); code.Get(base); StoreArrayField(place, 0);
            PrepareArrayLengthStore(place); code.I64((int64_t)count); StoreArrayLength(place);
        }
        if (prefix) { code.Get(base); code.I64(prefix); code.Byte(0x7c); code.Set(base); }
    }
    if (!count) return;
    auto source = module.Data(literal->val);
    CopyBytes({array->arr->sub, base, 0, memory, true, true},
              {array->arr->sub, NoLocal, (uint32_t)source, 0, false, true},
              (uint32_t)count, literal->line, true);
}

inline void WasmCodeGen::InitFilledArray(VarDef *owner, const Slot *slot, ArrayLit *literal,
                                        const FreshFixedDestination *fresh) {
    auto destination = fresh ? &fresh->place : nullptr;
    auto array = destination ? destination->type : owner->type;
    auto element = array->arr->sub;
    auto line = owner ? owner->line : literal->line;
    auto countnode = Is<IntLit>(literal->fillcount);
    if (!countnode || countnode->val < 0)
        Fail(literal->line, "array fill needs a nonnegative constant count");
    auto count = (uint64_t)countnode->val;
    auto stride = Size(element);
    auto prefix = DataArray(array) ? DataPrefix(array, count) : 0u;
    if (count > (UINT32_MAX - prefix) / stride)
        Fail(line, "array allocation exceeds memory32");
    if (prefix && prefix < 8 && count > ((1ull << (prefix * 8)) - 1))
        Fail(line, "array length exceeds its stored prefix");
    auto memory = ArrayAllocationMemory(owner, slot, destination, line);
    if (destination && fixedfillbase == NoLocal) fixedfillbase = Local(WasmModule::I64);
    auto base = destination ? fixedfillbase : Local(WasmModule::I64);
    if (InlineArray(array)) {
        auto capacity = (uint64_t)ArrSize(array->arr);
        if (count > capacity || (array->arr->akind == A_FIXED && count != capacity))
            Fail(line, "array fill does not fit its static layout");
        if (destination) {
            if (array->arr->akind == A_LIMITED)
                InitArrayCount(FreshArrayPlace(*fresh, literal->line), count);
        } else {
            auto header = Local(WasmModule::I32);
            Address(*slot); code.Set(header);
            if (array->arr->akind == A_LIMITED) {
                auto place = ArrayFromPlace({array, header, 0, memory, false, true}, literal->line);
                PrepareArrayLengthStore(place); code.I64((int64_t)count); StoreArrayLength(place);
            }
            code.Get(header);
            if (array->arr->akind == A_LIMITED) {
                code.I32((int32_t)IntSize(LenStore(array->arr))); code.Byte(0x6a);
            }
            code.Byte(0xad); code.Set(base);
        }
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
        if (DataArray(array)) {
            code.Get(base); Write(*slot);
            InitArrayCount(ArrayOwner(owner, {array, base, 0, memory, true, true}, literal->line), count);
        } else {
            auto place = FrameArrayOwner(owner, *slot, literal->line);
            PrepareArrayFieldStore(place, 0); code.Get(base); StoreArrayField(place, 0);
            PrepareArrayLengthStore(place); code.I64((int64_t)count); StoreArrayLength(place);
        }
    }
    // The language evaluates even a zero-count fill once. Capturing before
    // the loop also keeps reference targets and call side effects stable.
    auto item = NoLocal;
    if (destination) {
        auto &cached = fixedfillitems[WasmModule::I32 - Type(element)];
        if (cached == NoLocal) cached = Temp(element);
        item = cached;
    } else item = Temp(element);
    Gen(literal->fillval); Convert(literal->fillval->exprtype, element); code.Set(item);
    if (!count) return;
    if (destination) {
        // Nested initialization has finished before these shared loop locals are set.
        EmitPackedAddress(*destination, literal->line);
        if (array->arr->akind == A_LIMITED) {
            code.I64(IntSize(LenStore(array->arr))); code.Byte(0x7c);
        }
        code.Set(base);
        if (fixedfillposition == NoLocal) fixedfillposition = Local(WasmModule::I64);
    }
    auto position = destination ? fixedfillposition : Local(WasmModule::I64);
    code.I64(0); code.Set(position);
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

inline void WasmCodeGen::InitDataArray(VarDef *owner, const Slot &slot, ArrayLit *literal) {
    auto array = owner->type, element = array->arr->sub;
    auto count = literal->elems.size();
    auto prefix = DataPrefix(array, count), stride = Size(element);
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
    auto place = ArrayOwner(owner, {array, header, 0, memory, true, true}, literal->line);
    InitArrayCount(place, count);
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

inline WasmCodeGen::FreshDataArrayDestination WasmCodeGen::ReserveFreshDataArray(
        VarDef *owner, const Slot &slot, VarDecl *initialization, uint32_t count,
        uint32_t literalCount) {
    auto array = owner->type;
    if (!support.DataNominalArray(array) || !initialization || initialization->inline_arg ||
        find(initialization->defs.begin(), initialization->defs.end(), owner) == initialization->defs.end() ||
        !storage.owners.count(owner) || !TEq(slot.type, array))
        Fail(owner->line, "aggregate data construction needs its checked fresh declaration");
    auto stride = RequireFixed(array->arr->sub, owner->line), prefix = DataPrefix(array);
    if (!stride || prefix != 4) Fail(owner->line, "aggregate data construction needs a positive fixed u32 layout");
    uint32_t ownerBytes = 0;
    auto bytes = NoLocal;
    if (literalCount != NoLocal) {
        if (count != NoLocal || literalCount > (UINT32_MAX - prefix) / stride)
            Fail(owner->line, "aggregate data literal exceeds memory32");
        ownerBytes = prefix + literalCount * stride;
    } else {
        if (count == NoLocal) Fail(owner->line, "aggregate data copy is missing its captured count");
        code.Get(count); code.I64((UINT32_MAX - prefix) / stride); code.Byte(0x56);
        Open(0x04); Trap(6, owner->line); Close();
        bytes = Local(WasmModule::I32);
        code.Get(count); code.I64(stride); code.Byte(0x7e);
        code.I64(prefix); code.Byte(0x7c); code.Byte(0xa7); code.Set(bytes);
    }
    auto memory = storage.Memory(owner, current);
    auto identity = Local(WasmModule::I32), saved = Local(WasmModule::I32);
    if (memory >= 0) code.I32(memory); else StackIndex(storage.owners.at(owner) + 1);
    code.Set(identity);
    if (memory < 0) code.Get(identity);
    if (bytes == NoLocal) code.I32((int32_t)ownerBytes); else code.Get(bytes);
    code.Call(memory >= 0 ? memories->Reserve((uint32_t)memory) : memories->ReserveDynamic());
    code.Set(saved);
    if (!owner->isglobal) {
        assert(!scopes.empty());
        scopes.back().push_back({nullptr, memory >= 0 ? (uint32_t)memory : identity, saved, memory < 0});
    }
    auto header = Local(WasmModule::I64);
    code.Get(identity); code.Byte(0xad); code.I64(32); code.Byte(0x86);
    code.Get(saved); code.Byte(0xad); code.Byte(0x84); code.Set(header);
    code.Get(header); Write(slot);
    // Only now may callers store a prefix or construct a child image.
    auto image = ArrayOwner(owner, {array, header, 0, memory, true, true}, owner->line);
    return {image, owner, initialization, storage.owners.at(owner), identity, saved, bytes, count,
            prefix, stride, literalCount, ownerBytes};
}

inline void WasmCodeGen::InitAggregateDataArray(VarDef *owner, const Slot &slot,
                                              VarDecl *declaration, Node *source) {
    if (auto literal = Is<ArrayLit>(source)) {
        if (literal->fillval || literal->capexpr)
            Fail(source->line, "aggregate data fills need the pending snapshot lowering");
        if (literal->elems.size() >= NoLocal)
            Fail(source->line, "aggregate data literal exceeds memory32");
        auto fresh = ReserveFreshDataArray(owner, slot, declaration, NoLocal,
                                           (uint32_t)literal->elems.size());
        InitArrayCount(fresh.image, literal->elems.size());
        for (uint32_t i = 0; i < literal->elems.size(); i++)
            ConstructFixed(FreshDataElement(fresh, i, source->line), literal->elems[i]);
        return;
    }
    auto from = ActualType(source);
    while (from && from->kind == TY_REF) from = from->ref->sub;
    if (!from || !TEq(owner->type, from))
        Fail(source->line, "aggregate data adaptation needs the pending destination lowering");
    auto captured = ResolveArray(source);
    auto count = Local(WasmModule::I64);
    ArrayLength(captured); code.Set(count);
    auto fresh = ReserveFreshDataArray(owner, slot, declaration, count);
    CopyBytes(fresh.image.image, captured.image, fresh.bytesLocal, source->line);
}

inline void WasmCodeGen::InitArray(VarDef *owner, const Slot &slot, Node *init, VarDecl *declaration) {
    if (owner->reusable) Fail(owner->line, "pool owners need the pending descriptor lowering");
    auto resultCall = Is<Call>(init);
    if (InlineArray(owner->type) &&
        ((((resultCall && resultCall->builtin < 0) || Is<InlineBlock>(init)) && FixedResult(ActualType(init))) ||
         Is<Block>(init) || Is<IfExpr>(init) ||
         (Is<Unary>(init) && Is<Unary>(init)->op == T_MINUS && HasFixedTemporary(init)) ||
         FixedBinary(init) ||
         ((Is<Dot>(init) || Is<Index>(init)) && HasFixedTemporary(init)))) {
        ConstructFixed(FreshOwner(owner, declaration), init); return;
    }
    if (auto call = Is<Call>(init); call && call->builtin == B_DEFAULT && InlineArray(owner->type)) {
        ConstructFixed(FreshOwner(owner, declaration), init); return;
    }
    while (auto call = Is<Call>(init)) {
        if (call->defaultinit) init = call->defaultinit;
        else if (call->builtin == B_COPY) init = call->ValueArgNodes().at(0);
        else break;
    }
    if (support.DataNominalArray(owner->type)) {
        InitAggregateDataArray(owner, slot, declaration, init); return;
    }
    if (auto literal = Is<StrLit>(init)) { InitByteString(owner, &slot, literal); return; }
    auto literal = Is<ArrayLit>(init);
    if (!literal) { InitArrayCopy(owner, slot, init); return; }
    auto array = owner->type;
    if (InlineArray(array) && Nominal(array->arr->sub)) {
        ConstructAggregateArray(FreshOwner(owner, declaration), literal); return;
    }
    if (literal->capexpr) { InitLimitedCapacity(owner, slot, literal); return; }
    if (literal->fillval) { InitFilledArray(owner, &slot, literal); return; }
    if (DataArray(array)) { InitDataArray(owner, slot, literal); return; }
    if (!IsResz(array)) {
        auto header = Local(WasmModule::I32);
        Address(slot); code.Set(header);
        InlineArrayLiteral(ArrayOwner(owner, {array, header, 0, 0, false, true}, literal->line), literal);
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
    auto place = ArrayOwner(owner, {array, header, 0, 0, false, true}, literal->line);
    PrepareArrayFieldStore(place, 0); code.Get(identity); code.Byte(0xad); code.I64(32); code.Byte(0x86);
    code.Get(saved); code.Byte(0xad); code.Byte(0x84); StoreArrayField(place, 0);
    PrepareArrayLengthStore(place); code.I64(0); StoreArrayLength(place);
    for (auto value : literal->elems)
        PushArray(place, value, nullptr, value->line);
}

inline void WasmCodeGen::LoadElement(const ElementPlace &place) {
    auto element = place.type;
    if (Aggregate(element)) Fail(element->line, "aggregate element reads need a stored-value consumer");
    if (place.memory >= 0) { code.Byte(0xa7); LoadFixed(element, (uint32_t)place.memory); }
    else Load(element);
}

inline void WasmCodeGen::StoreElement(const ElementPlace &place) {
    auto element = place.type;
    if (Aggregate(element)) Fail(element->line, "whole-aggregate assignment needs the pending destination lowering");
    if (place.memory >= 0) {
        auto value = Temp(element); code.Set(value); code.Byte(0xa7); code.Get(value);
        StoreFixed(element, (uint32_t)place.memory);
    } else Store(element);
}

inline void WasmCodeGen::PushArray(const ArrayPlace &place, Node *value,
                                  TypeExpr *result, Line line, PushScratch *scratch) {
    auto element = place.layout.element;
    auto header = place.image.address; auto memory = place.elementMemory;
    Gen(value); Convert(value->exprtype, element);
    auto item = scratch ? scratch->item : Temp(element); code.Set(item);
    // Capture the receiver before argument effects, but read its count after them.
    auto length = scratch ? scratch->length : Local(WasmModule::I64);
    auto old = scratch ? scratch->old : Local(WasmModule::I32);
    ArrayLength(place); code.Set(length);
    if (place.layout.image == ArrayImage::GrowableHeader) {
        if (memory >= 0) { code.I32((int32_t)place.layout.stride); code.Call(memories->Reserve(memory)); }
        else {
            code.Get(header); code.Mem(0x29); code.I64(32); code.Byte(0x88); code.Byte(0xa7);
            code.I32((int32_t)place.layout.stride); code.Call(memories->ReserveDynamic());
        }
        code.Set(old);
        code.Get(header); code.Mem(0x29); code.I64(-4294967296ll); code.Byte(0x83);
        code.Get(old); code.Byte(0xad); code.Byte(0x84);
    } else {
        code.Get(length); ArrayCapacity(place); code.Byte(0x5a);
        Open(0x04); Trap(10, line); Close();
        ElementOffset({place}, length, line, scratch);
    }
    auto address = scratch ? scratch->address : Local(WasmModule::I64);
    if (scratch && memory >= 0) {
        code.Set(address); code.Get(address); code.Byte(0xa7); code.Get(item);
        StoreFixed(element, (uint32_t)memory);
    } else { code.Tee(address); code.Get(item); StoreElement({element, memory}); }
    PrepareArrayLengthStore(place); code.Get(length); code.I64(1); code.Byte(0x7c); StoreArrayLength(place);
    if (!Void(result)) {
        code.Get(address);
        if (result->kind != TY_REF || !TEq(result->ref->sub, element)) {
            LoadElement({element, memory}); Convert(element, result);
        } else if (Type(result) == WasmModule::I32) code.Byte(0xa7);
    }
}

inline void WasmCodeGen::ElementOffset(const ArrayView &view, uint32_t index, Line line,
                                     PushScratch *scratch) {
    const auto &place = view.place;
    const auto &layout = place.layout;
    auto base = scratch ? scratch->base : Local(WasmModule::I64);
    auto offset = scratch ? scratch->offset : Local(WasmModule::I64);
    if (layout.image == ArrayImage::GrowableHeader) {
        if (place.ownerSlot) { Address(*place.ownerSlot); code.Mem(0x29); }
        else { code.Get(place.image.address); code.Mem(0x29, 0, place.image.offset); }
    } else if (!place.image.packed) {
        EmitKnownOffset(place.image, (uint32_t)place.image.memory, line);
        if (layout.prefix.elements > 0) {
            code.I32((int32_t)layout.prefix.elements); code.Byte(0x6a);
        }
        code.Byte(0xad);
        if (place.image.memory > 0) {
            code.I64((int64_t)place.image.memory << 32); code.Byte(0x84);
        }
    } else EmitPackedAddress(place.image, line);
    code.Set(base);
    code.Get(base); code.I64(UINT32_MAX); code.Byte(0x83);
    if (layout.varint) {
        if (view.prefixBytes != NoLocal) code.Get(view.prefixBytes);
        else {
            EmitPackedAddress(place.image, line); code.Call(memories->ReadPrefix());
            auto width = Local(WasmModule::I32); code.Set(width); code.Byte(0x1a); code.Get(width);
        }
        code.Byte(0xad); code.Byte(0x7c);
    } else if (place.image.packed && layout.prefix.elements > 0) {
        code.I64(layout.prefix.elements); code.Byte(0x7c);
    }
    code.Get(index); code.I64(layout.stride); code.Byte(0x7e); code.Byte(0x7c); code.Tee(offset);
    code.I64(UINT32_MAX); code.Byte(0x56); Open(0x04); Trap(11, line); Close();
    code.Get(base); code.I64(-4294967296ll); code.Byte(0x83); code.Get(offset); code.Byte(0x84);
}

inline WasmCodeGen::ElementPlace WasmCodeGen::ElementAddress(Index *index) {
    return ElementAddress(index, ResolveArray(index->obj));
}

inline WasmCodeGen::ElementPlace WasmCodeGen::ElementAddress(Index *index, const ArrayPlace &place) {
    // Capture before index statements; the current admitted bases are stable.
    auto length = Local(WasmModule::I64), position = Local(WasmModule::I64);
    auto prefix = place.layout.varint ? Local(WasmModule::I32) : NoLocal;
    auto view = CaptureArrayView(place, length, prefix);
    Gen(index->idx); code.Set(position);
    if (!index->nobc) {
        code.Get(position); code.Get(length); code.Byte(0x5a);
        Open(0x04); Trap(8, index->line); Close();
    }
    ElementOffset(view, position, index->line);
    return {place.layout.element, place.elementMemory, true};
}

inline WasmCodeGen::FixedPlace WasmCodeGen::CaptureElementPlace(const ElementPlace &element) {
    auto address = Local(WasmModule::I64); code.Set(address);
    return {element.type, address, 0, element.memory, true, element.bounded};
}

inline void WasmCodeGen::AssignElement(Index *index, Node *rhs, TType op, bool pointee, Line line) {
    auto selected = ElementAddress(index);
    auto type = selected.type; auto memory = selected.memory;
    if (Nominal(type) || InlineArray(type)) { AssignFixed(CaptureElementPlace(selected), rhs, op, line); return; }
    auto address = Local(WasmModule::I64); code.Set(address);
    if (pointee && type->kind == TY_REF && op != T_DOTASSIGN) {
        code.Get(address); LoadElement({type, memory});
        if (Nominal(type->ref->sub) || InlineArray(type->ref->sub)) {
            auto destination = PointeePlace(type, line);
            AssignFixed(destination, rhs, op, line); return;
        }
        CheckNull(line, Type(type));
        if (type->ref->sub->kind == TY_ARRAY) Fail(line, "whole-array assignment needs the pending destination lowering");
        if (Nominal(type->ref->sub)) Fail(line, "whole-aggregate assignment needs the pending destination lowering");
        if (Type(type) == WasmModule::I32) address = Local(WasmModule::I32);
        code.Set(address); type = type->ref->sub; memory = -1;
    }
    if (op == T_DOTASSIGN) {
        if (type->kind != TY_REF) Fail(line, "reference rebinding requires a reference element");
        if (auto source = Is<Ident>(rhs); source && source->vdef && source->vdef->type->kind != TY_REF) {
            ReferenceAddress(Find(source->vdef));
        } else ReferenceValue(rhs, Type(type));
    } else {
        if (op != T_ASSIGN) { code.Get(address); LoadElement({type, memory}); }
        if (rhs) { Gen(rhs); Convert(rhs->exprtype, type); }
        else if (type->kind == TY_FLT) {
            if (type->fltstorage == FS_F32) code.F32(1); else code.F64(1);
        } else code.I64(1);
        if (op != T_ASSIGN) Arithmetic(op, type, line);
    }
    auto value = Temp(type); code.Set(value); code.Get(address); code.Get(value); StoreElement({type, memory});
}

inline void WasmCodeGen::ArrayBuiltin(Call *call, const vector<Node *> &arguments, TypeExpr *resulttype) {
    auto array = ArrayType(arguments[0]), element = array->arr->sub;
    auto place = ResolveArray(arguments[0]);
    auto header = place.image.address; auto memory = place.elementMemory;
    if (call->builtin == B_LEN) { ArrayLength(place); return; }
    if (VariableArray(array)) Fail(call->line, "variable-array mutation needs the pending destination lowering");
    if (call->builtin == B_CAP) { ArrayCapacity(place); return; }
    if (Nominal(element) && (call->builtin == B_PUSH || call->builtin == B_POP))
        Fail(call->line, "aggregate push/pop needs the pending destination lowering");
    if (call->builtin == B_PUSH) {
        PushArray(place, arguments[1], resulttype ? resulttype : call->exprtype, call->line); return;
    }
    auto length = Local(WasmModule::I64);
    ArrayLength(place); code.Set(length);
    if (call->builtin == B_POP) {
        code.Get(length); code.Byte(0x50); Open(0x04); Trap(9, call->line); Close();
        code.Get(length); code.I64(1); code.Byte(0x7d); code.Set(length);
    } else { code.I64(0); code.Set(length); }
    ElementOffset({place}, length, call->line);
    auto address = Local(WasmModule::I64); code.Set(address);
    int result = -1;
    if (call->builtin == B_POP) {
        result = (int)Temp(element); code.Get(address); LoadElement({element, memory}); code.Set(result);
    }
    if (place.layout.image == ArrayImage::GrowableHeader && memory >= 0) {
        code.Get(address); code.Byte(0xa7); code.Byte(0x24); code.U(memory);
    } else if (place.layout.image == ArrayImage::GrowableHeader) {
        code.Get(header); code.Mem(0x29); code.I64(32); code.Byte(0x88); code.Byte(0xa7);
        code.Get(address); code.Byte(0xa7); code.Call(memories->Top(true));
    }
    PrepareArrayLengthStore(place); code.Get(length); StoreArrayLength(place);
    if (result >= 0) { code.Get(result); Convert(element, resulttype ? resulttype : call->exprtype); }
}

inline void WasmCodeGen::ArrayEquality(Binary *node) {
    Node *leftnode = node->left, *rightnode = node->right;
    auto leftslice = Is<SliceExpr>(leftnode), rightslice = Is<SliceExpr>(rightnode);
    auto view = leftslice || rightslice;
    if (view) {
        if (!leftslice || !rightslice || !leftslice->cmpview || !rightslice->cmpview ||
            leftslice->lo || leftslice->hi || rightslice->lo || rightslice->hi ||
            leftslice->lo_from_end || leftslice->hi_from_end ||
            rightslice->lo_from_end || rightslice->hi_from_end)
            Fail(node->line, "slice equality needs the pending view lowering");
        leftnode = leftslice->obj; rightnode = rightslice->obj;
    }
    auto scoped = view || HasFixedTemporary(leftnode) || HasFixedTemporary(rightnode) ||
                  ArrayPathHasStatements(rightnode);
    auto lefttype = ArrayType(leftnode), righttype = ArrayType(rightnode);
    if (view && (!InlineArray(lefttype) || !InlineArray(righttype)))
        Fail(node->line, "comparison views need the pending nonfixed owner lowering");
    if (Nominal(lefttype->arr->sub) || Nominal(righttype->arr->sub))
        Fail(node->line, "aggregate array equality needs the pending value lowering");
    auto element = lefttype->arr->sub;
    auto compare = [&](const ArrayView &leftview, const ArrayView &rightview, uint32_t length) {
        auto result = Local(WasmModule::I32), position = Local(WasmModule::I64);
        code.I32(0); code.Set(result);
        code.Get(length); ViewLength(rightview); code.Byte(0x51); Open(0x04);
        code.I32(1); code.Set(result); code.I64(0); code.Set(position);
        auto done = Open(), head = Open(0x03);
        code.Get(position); code.Get(length); code.Byte(0x5a); Branch(done, true);
        ElementOffset(leftview, position, node->line); LoadElement({element, leftview.place.elementMemory});
        ElementOffset(rightview, position, node->line); LoadElement({rightview.place.layout.element, rightview.place.elementMemory});
        auto type = Type(element);
        code.Byte(type == WasmModule::F32 ? 0x5b : type == WasmModule::F64 ? 0x61 :
                  type == WasmModule::I32 ? 0x46 : 0x51);
        code.Byte(0x45); Open(0x04);
        code.I32(0); code.Set(result); Branch(done); Close();
        code.Get(position); code.I64(1); code.Byte(0x7c); code.Set(position);
        Branch(head); Close(); Close(); Close();
        code.Get(result);
        if (node->op == T_NEQ) code.Byte(0x45);
    };
    if (scoped) {
        if (!InlineArray(lefttype))
            Fail(node->line, "effectful array comparison needs the pending destination lowering");
        auto result = Local(WasmModule::I32);
        auto evaluateRight = [&](const ArrayPlace &left) {
            auto length = Local(WasmModule::I64);
            auto leftprefix = VarintPrefix(lefttype) ? Local(WasmModule::I32) : NoLocal;
            auto rightprefix = VarintPrefix(righttype) ? Local(WasmModule::I32) : NoLocal;
            auto leftview = CaptureArrayView(left, length, leftprefix);
            auto finish = [&](const ArrayPlace &right) {
                compare(leftview, {right, NoLocal, rightprefix}, length);
                code.Set(result);
            };
            if (HasFixedTemporary(rightnode)) {
                WithReadPlace(rightnode, [&](FixedPlace selected) {
                    while (selected.type->kind == TY_REF) selected = DereferencePlace(selected, node->line);
                    finish(ArrayFromPlace(selected, node->line));
                });
            } else finish(ResolveArray(rightnode));
        };
        if (view) {
            // Frontend comparison slices retain a view, including temporary owners.
            if (HasFixedTemporary(leftnode)) {
                WithReadPlace(leftnode, [&](FixedPlace selected) {
                    while (selected.type->kind == TY_REF) selected = DereferencePlace(selected, node->line);
                    evaluateRight(ArrayFromPlace(selected, node->line));
                });
            } else evaluateRight(ResolveArray(leftnode));
        } else {
            // Same-type array equality captures a value before the right operand.
            WithFixedTemporary(lefttype, leftnode, [&](const FixedPlace &image) {
                evaluateRight(ArrayFromPlace(image, node->line));
            });
        }
        code.Get(result);
        return;
    }
    auto left = ResolveArray(leftnode); auto length = Local(WasmModule::I64);
    auto leftprefix = VarintPrefix(lefttype) ? Local(WasmModule::I32) : NoLocal;
    auto rightprefix = VarintPrefix(righttype) ? Local(WasmModule::I32) : NoLocal;
    auto leftview = CaptureArrayView(left, length, leftprefix);
    auto right = ResolveArray(rightnode); ArrayView rightview {right, NoLocal, rightprefix};
    compare(leftview, rightview, length);
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
            // Freeze the parent before index statements; child reference slots still reload.
            auto parent = LoadArrayWalk(walk);
            step.length = Local(WasmModule::I64);
            CaptureArrayView(parent, step.length);
            walk.root = nullptr; walk.captured = parent; walk.steps.clear();
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
    else walk.captured = ResolveArray(n);
}

inline WasmCodeGen::ArrayPlace WasmCodeGen::LoadArrayWalk(const ArrayWalk &walk) {
    assert(walk.root || walk.captured);
    auto place = walk.root ? ResolveArray(walk.root) : *walk.captured;
    for (auto &step : walk.steps) {
        auto index = step.node;
        auto array = ArrayType(index->obj), element = array->arr->sub;
        if (element->kind != TY_REF || element->ref->sub->kind != TY_ARRAY)
            Fail(index->line, "this array path needs the pending compound lowering");
        if (!index->nobc) {
            code.Get(step.position);
            ViewLength({place, step.length});
            code.Byte(0x5a); Open(0x04); Trap(8, index->line); Close();
        }
        ElementOffset({place}, step.position, index->line);
        LoadElement({element, place.elementMemory}); CheckNull(index->line, Type(element));
        auto address = Local(Type(element)); code.Set(address);
        // The loaded reference establishes its own target domain, not the slot's domain.
        place = ArrayFromReference(element, address, index->line);
    }
    return place;
}

inline void WasmCodeGen::CapturePlaceWalk(Node *n, PlaceWalk &walk) {
    if (auto field = Is<Dot>(n); field && field->IsField()) {
        CapturePlaceWalk(field->obj, walk);
        walk.steps.push_back({field});
        return;
    }
    if (auto index = Is<Index>(n)) {
        CapturePlaceWalk(index->obj, walk);
        PlaceWalkStep step {index, Local(WasmModule::I64)};
        if (ArrayPathHasStatements(index->idx)) {
            // Index effects see the captured parent; subsequent path slots still reload.
            auto parent = LoadPlaceWalk(walk);
            step.length = Local(WasmModule::I64);
            CaptureArrayView(ArrayFromPlace(parent, index->line), step.length);
            walk.root = nullptr; walk.captured = parent; walk.steps.clear();
        }
        Gen(index->idx); code.Set(step.position);
        walk.steps.push_back(step);
        return;
    }
    if (auto address = Is<Unary>(n); address && address->op == T_BITAND &&
        address->child->exprtype->kind != TY_REF &&
        (Is<Ident>(address->child) || Is<Dot>(address->child) || Is<Index>(address->child))) {
        CapturePlaceWalk(address->child, walk); return;
    }
    auto id = Is<Ident>(n);
    if (id && id->vdef && id->vdef->isvar && id->vdef->type->kind == TY_REF) walk.root = n;
    else walk.captured = ResolvePlace(n);
}

inline WasmCodeGen::FixedPlace WasmCodeGen::LoadPlaceWalk(const PlaceWalk &walk) {
    assert(walk.root || walk.captured);
    auto place = walk.root ? ResolvePlace(walk.root) : *walk.captured;
    for (auto &step : walk.steps) {
        if (auto field = Is<Dot>(step.node)) {
            auto [type, offset] = StoredField(place.type, field->fieldidx, field->line);
            if (field->accessorowner && !TEq(field->accessorowner, place.type))
                Fail(field->line, "field adaptation needs the pending layout lowering");
            if ((uint64_t)offset > UINT32_MAX - place.offset)
                Fail(field->line, "field offset exceeds memory32");
            place.offset += (uint32_t)offset; place.type = type;
        } else {
            auto index = Is<Index>(step.node); assert(index);
            auto array = ArrayFromPlace(place, index->line);
            if (!index->nobc) {
                code.Get(step.position); ViewLength({array, step.length});
                code.Byte(0x5a); Open(0x04); Trap(8, index->line); Close();
            }
            ElementOffset({array}, step.position, index->line);
            place = CaptureElementPlace({array.layout.element, array.elementMemory, true});
        }
        while (place.type->kind == TY_REF) place = DereferencePlace(place, step.node->line);
    }
    return place;
}

inline void WasmCodeGen::ArrayFor(ForLoop *loop) {
    auto array = ArrayType(loop->iter), element = array->arr->sub;
    auto id = Is<Ident>(loop->iter);
    auto reload = id && id->vdef && id->vdef->isvar && id->vdef->type->kind == TY_REF;
    optional<ArrayWalk> walk;
    optional<PlaceWalk> fields;
    if (FieldPath(loop->iter)) { fields.emplace(); CapturePlaceWalk(loop->iter, *fields); }
    else if (Is<Index>(loop->iter)) { walk.emplace(); CaptureArrayWalk(loop->iter, *walk); }
    auto place = reload || walk || fields
        ? CaptureArrayBorrow(array, Local(BorrowedArrayAddressType(array)), BorrowedArrayAddressType(array),
                             ArrayOrigin::ReferenceABI, loop->line)
        : ResolveArray(loop->iter);
    auto header = place.image.address;
    auto memory = place.elementMemory;
    auto copyAggregate = Nominal(loop->vdef->type);
    if (copyAggregate) {
        auto plan = storage.fixedvalues.find(loop->vdef);
        if (loop->iterkind != IK_ARRAY || loop->byref || !loop->vdef->copybind ||
            !(InlineArray(array) || support.DataNominalArray(array)) || !Nominal(element) ||
            !TEq(element, loop->vdef->type) || plan == storage.fixedvalues.end() ||
            plan->second.origin != WasmStoragePlan::FixedOrigin::IterationCopy ||
            plan->second.initialization != loop || !RequireFixed(element, loop->line))
            Fail(loop->line, "by-value aggregate iteration needs a fixed Memory 0 copy owner");
        if (InlineArray(array)) RequireFixed(array, loop->line);
    }
    auto prefix = VarintPrefix(array) ? (int)Local(WasmModule::I32) : -1;
    auto position = Local(WasmModule::I64); code.I64(0); code.Set(position);
    auto end = Open(), head = Open(0x03);
    if (fields) {
        auto selected = LoadPlaceWalk(*fields);
        PlaceAddress(selected, BorrowedArrayAddressType(array), loop->line); code.Set(header);
    } else if (walk) {
        auto selected = LoadArrayWalk(*walk); code.Get(selected.image.address); code.Set(header);
    } else if (reload) {
        auto selected = ResolveArray(loop->iter); code.Get(selected.image.address); code.Set(header);
    }
    // Growth during iteration is permitted. Read the current count on each
    // test rather than assuming the entry view has a fixed length.
    code.Get(position); ArrayLength(place, prefix); code.Byte(0x5a); Branch(end, true);
    ElementOffset({place, NoLocal, prefix < 0 ? NoLocal : (uint32_t)prefix}, position, loop->line);
    if (copyAggregate) {
        auto selected = CaptureElementPlace({element, memory});
        // The current length test and valid complete source image bound the whole element.
        CopyFixed(FreshOwner(loop->vdef, loop), selected, loop->line);
    } else {
        if (!loop->byref || element->kind == TY_REF) {
            LoadElement({element, memory}); Convert(element, loop->vdef->type);
        } else if (Type(loop->vdef->type) == WasmModule::I32) code.Byte(0xa7);
        Write(Find(loop->vdef));
    }
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
