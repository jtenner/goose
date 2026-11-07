// Exercise checked sizes without allocating their declared byte images.
#include "../src/includes.h"
#include "../src/utils.h"
#include "../src/small_vector.h"
#include "../src/flat_map.h"
#include "../src/lexer.h"
#include "../src/ast.h"
#include "../src/value_layout.h"
#include "../src/wasm_support.h"

int main() {
    using namespace goose;
    ValueLayout layout;
    ValueLayout::FixedSizes sizes;
    uint64_t bytes = 0;
    TypeExpr byte(TY_INT, {}), word(TY_INT, {}), half(TY_INT, {}), wide(TY_INT, {});
    byte.intstorage = IS_U8; word.intstorage = IS_U32;
    half.intstorage = IS_I16; wide.intstorage = IS_U64;
    struct Fixed {
        SStruct declaration;
        StructInst instance;
        TypeStruct detail;
        TypeExpr type {TY_STRUCT, {}};
        Fixed(std::initializer_list<TypeExpr *> fields) {
            instance.st = &declaration; detail.st = &declaration; detail.inst = &instance;
            type.struc = &detail;
            for (auto t : fields) {
                Field field; field.type = t; field.ispad = !t;
                declaration.fields.push_back(field); instance.ftypes.push_back(t);
            }
        }
    } padded {&byte, nullptr, &word, nullptr, &half};
    padded.declaration.fields[3].padsize = 3;
    assert(!layout.TryFixedSize(&padded.type, 12, bytes, sizes));
    assert(!layout.layouts.count({&padded.instance, -1}));
    assert(layout.TryFixedSize(&padded.type, 13, bytes, sizes) && bytes == 13);
    assert((layout.StructLayout(&padded.instance).offs == vector<int64_t> {0, 1, 4, 8, 11}));
    assert(!layout.TryFixedSize(&padded.type, 12, bytes, sizes)); // Cached sizes obey each limit.
    Fixed empty {};
    assert(!layout.TryFixedSize(&empty.type, 0, bytes, sizes));
    assert(layout.TryFixedSize(&empty.type, 1, bytes, sizes) && bytes == 1);
    TypeExpr array(TY_ARRAY, {}); TypeArray elements;
    array.arr = &elements; elements.sub = &byte; elements.size = UINT32_MAX;
    assert(layout.TryFixedSize(&array, UINT32_MAX, bytes, sizes) && bytes == UINT32_MAX);
    assert(!layout.TryFixedSize(&array, UINT32_MAX - 1, bytes, sizes));
    TypeExpr large(TY_ARRAY, {}); TypeArray largeElements;
    large.arr = &largeElements; largeElements.sub = &wide; largeElements.size = INT64_MAX;
    assert(!layout.TryFixedSize(&large, UINT32_MAX, bytes, sizes));
    assert(!sizes.count(&large));
    Fixed sum {&array, &byte};
    assert(!layout.TryFixedSize(&sum.type, UINT32_MAX, bytes, sizes));
    assert(!layout.layouts.count({&sum.instance, -1}));
    TypeExpr next(TY_REF, {}); TypeRef pointer; next.ref = &pointer;
    Fixed recursive {&next, &byte}; pointer.sub = &recursive.type; pointer.optional = true;
    assert(layout.TryFixedSize(&recursive.type, UINT32_MAX, bytes, sizes) && bytes == 9);
    WasmValueSupport support(layout);
    assert(!support.Check(&recursive.type));
    TypeExpr relative(TY_REF, {}); TypeRef rel;
    relative.ref = &rel; rel.sub = &byte; rel.lenstorage = IS_U32;
    Fixed rejected {&next, &relative};
    WasmValueSupport fresh(layout);
    assert(fresh.Check(&rejected.type));
    assert(fresh.validated.empty()); // A cycle must not cache provisional success.
    TypeExpr grow(TY_ARRAY, {}); TypeArray growElements;
    grow.arr = &growElements; growElements.sub = &byte; growElements.akind = A_GROW;
    TypeExpr growRef(TY_REF, {}); TypeRef growPointer;
    growRef.ref = &growPointer; growPointer.sub = &grow;
    assert(layout.TryFixedSize(&growRef, 16, bytes, sizes) && bytes == 16);
    assert(layout.TryFixedSize(&next, 8, bytes, sizes) && bytes == 8);
    assert(!layout.TryFixedSize(&growRef, 15, bytes, sizes));
    struct Enum {
        SEnum declaration;
        EnumInst instance;
        TypeEnum detail;
        TypeExpr type {TY_ENUM, {}};
        TypeVariant selected;
        TypeExpr variant {TY_VARIANT, {}};
        Enum(size_t count, std::initializer_list<TypeExpr *> fields) {
            declaration.variants.resize(count); instance.vftypes.resize(count);
            instance.en = &declaration; detail.en = &declaration; detail.inst = &instance;
            type.enu = &detail; selected.adt = &type;
            selected.variant = &declaration.variants.back(); variant.var = &selected;
            for (auto t : fields) {
                Field field; field.type = t; field.ispad = !t;
                declaration.variants.back().fields.push_back(field);
                instance.vftypes.back().push_back(t);
            }
            for (size_t i = 0; i < count; i++)
                instance.runs.push_back({&declaration.variants[i].fields, &instance.vftypes[i]});
        }
    } tag8(256, {&word}), tag16(257, {&word}), tagOnly(1, {}), overflow(2, {&array});
    assert(layout.TryFixedSize(&tag8.type, 5, bytes, sizes) && bytes == 5);
    assert(layout.TagStore(&tag8.declaration) == IS_U8);
    assert(!layout.TryFixedSize(&tag16.type, 5, bytes, sizes));
    assert(layout.TryFixedSize(&tag16.type, 6, bytes, sizes) && bytes == 6);
    assert(layout.TagStore(&tag16.declaration) == IS_U16);
    assert(!layout.TryFixedSize(&tag16.type, 5, bytes, sizes));
    assert(layout.TryFixedSize(&tagOnly.variant, 0, bytes, sizes) && bytes == 0);
    assert(layout.TryFixedSize(&tagOnly.type, 1, bytes, sizes) && bytes == 1);
    assert(!layout.TryFixedSize(&overflow.type, UINT32_MAX, bytes, sizes));
    assert(!sizes.count(&overflow.type));
    Enum mixed(2, {&byte});
    mixed.instance.allfixed = false;
    Field growField; growField.type = &grow;
    mixed.declaration.variants[0].fields.push_back(growField);
    mixed.instance.vftypes[0].push_back(&grow);
    WasmValueSupport selectedOnly(layout);
    assert(!selectedOnly.Check(&mixed.variant));
    assert(selectedOnly.Check(&mixed.type));
    Enum bad(1, {&relative});
    WasmValueSupport badPayload(layout);
    assert(badPayload.Check(&bad.type) && badPayload.validated.empty());
    puts("checked fixed layouts: PASS");
}
