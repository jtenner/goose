// Use the driver header order so every AST virtual pass has its definition.
#include "../src/includes.h"
#include "../src/utils.h"
#include "../src/small_vector.h"
#include "../src/flat_map.h"
#include "../src/lexer.h"
#include "../src/ast.h"
#include "../src/dump.h"
#include "../src/clone.h"
#include "../src/parser.h"
#include "../src/resolve.h"
#include "../src/builtins.h"
#include "../src/gfx.h"
#include "../src/typecheck.h"
#include "../src/typecheck_types.h"
#include "../src/typecheck_exprs.h"
#include "../src/typecheck_expansion.h"
#include "../src/typecheck_flow.h"
#include "../src/typecheck_calls.h"
#include "../src/typecheck_builtins.h"
#include "../src/typecheck_nodes.h"
#include "../src/optimize.h"
#include "../src/optimize_basecase.h"
#include "../src/optimize_tre.h"
#include "../src/optimize_loops.h"
#include "../src/optimize_reassoc.h"
#include "../src/bce.h"
#include "../src/data_stacks.h"
#include "../src/value_layout.h"
#include "../src/codegen.h"
#include "../src/codegen_types.h"
#include "../src/codegen_frames.h"
#include "../src/codegen_values.h"
#include "../src/codegen_construct.h"
#include "../src/codegen_stmts.h"
#include "../src/codegen_calls.h"
#include "../src/codegen_builtins.h"
#include "../src/codegen_render.h"
#include "../src/codegen_emit.h"
#include "../src/codegen_stacks.h"
#include "../src/codegen_nodes.h"
#include "../src/runtime_inline.h"
#include "../src/wasm_binary.h"
#include "../src/wasm_memory.h"
#include "../src/wasm_support.h"
#include "../src/wasm_storage.h"
#include "../src/wasm_codegen.h"
#include "../src/wasm_arrays.h"
#include "../src/wasm_fixed.h"

int main(int argc, char **argv) {
    using namespace goose;
    if (argc != 2) return 2;
    Ast ast;
    WasmCodeGen gen(ast);
    gen.module.memories = 3;
    gen.storage.dataaddresses = true;
    gen.failfn = gen.module.ImportFn("fail_v1", {WasmModule::I32, WasmModule::I32,
                                               WasmModule::I32, WasmModule::I32}, {});
    gen.memories.emplace(gen.module, gen.failfn);
    auto byte = ast.inttypes[IS_U8];
    TypeExpr limited(TY_ARRAY, {}); TypeArray detail;
    limited.arr = &detail; detail.akind = A_LIMITED; detail.sub = byte;
    TypeExpr fixed(TY_ARRAY, {}); TypeArray fixedDetail;
    fixed.arr = &fixedDetail; fixedDetail.sub = byte; fixedDetail.size = 16;
    auto add = [&](const string &name, vector<uint8_t> params, vector<uint8_t> results, auto emit) {
        auto fn = gen.module.AddFn(name, std::move(params), std::move(results));
        gen.StartFunction(fn, nullptr);
        emit(); // WasmModule::Finish appends the function end.
        gen.EndFunction();
        gen.module.exports.push_back({name, 0, fn});
    };
    add("pack0", {WasmModule::I32}, {WasmModule::I64}, [&] {
        gen.EmitPackedAddress({byte, 0, 0, 0, false, false}, {});
    });
    add("pack2", {WasmModule::I32}, {WasmModule::I64}, [&] {
        gen.EmitPackedAddress({byte, 0, 0, 2, false, false}, {});
    });
    add("pack2off", {WasmModule::I32}, {WasmModule::I64}, [&] {
        gen.EmitPackedAddress({byte, 0, 7, 2, false, false}, {});
    });
    add("pack2bounded", {WasmModule::I32}, {WasmModule::I64}, [&] {
        gen.EmitPackedAddress({byte, 0, 7, 2, false, true}, {});
    });
    add("packconstant", {}, {WasmModule::I64}, [&] {
        gen.EmitPackedAddress({byte, gen.NoLocal, 32, 2, false, true}, {});
    });
    add("packedoff", {WasmModule::I64}, {WasmModule::I64}, [&] {
        gen.EmitPackedAddress({byte, 0, 7, -1, true, false}, {});
    });
    add("knownoff", {WasmModule::I64}, {WasmModule::I32}, [&] {
        gen.EmitKnownOffset({byte, 0, 7, 2, true, false}, 2, {});
    });
    add("thin0", {WasmModule::I64}, {WasmModule::I32}, [&] {
        gen.EmitMemoryZeroReference({byte, 0, 7, -1, true, false}, {});
    });
    for (auto [name, memory, packed] : vector<tuple<string, int, bool>> {
             {"thin", 2, false}, {"known", 2, true}, {"dynamic", -1, true}}) {
        auto pointer = packed ? WasmModule::I64 : WasmModule::I32;
        auto place = [&] { return gen.ArrayFromPlace({&limited, 0, 3, memory, packed, true}, {}); };
        add(name + "len", {pointer}, {WasmModule::I64}, [&] { gen.ArrayLength(place()); });
        add(name + "cap", {pointer}, {WasmModule::I64}, [&] { gen.ArrayCapacity(place()); });
        add(name + "store", {pointer, WasmModule::I64}, {}, [&] {
            auto p = place(); gen.PrepareArrayLengthStore(p); gen.code.Get(1); gen.StoreArrayLength(p);
        });
        add(name + "element", {pointer, WasmModule::I64}, {WasmModule::I64}, [&] {
            gen.ElementOffset({place()}, 1, {});
        });
    }
    for (auto [name, destination, source] : vector<tuple<string, int, int>> {
             {"copy00", 0, 0}, {"copy20", 2, 0}, {"copy02", 0, 2},
             {"copy0u", 0, -1}, {"copyu0", -1, 0}, {"copy2u", 2, -1},
             {"copyu2", -1, 2}, {"copyuu", -1, -1}}) {
        add(name, {WasmModule::I64, WasmModule::I64, WasmModule::I32}, {}, [&] {
            gen.CopyBytes({byte, 0, 0, destination, true, true},
                          {byte, 1, 0, source, true, true}, 2, {});
        });
    }
    add("copyconstant", {WasmModule::I64}, {}, [&] {
        gen.CopyBytes({byte, 0, 0, -1, true, true}, {byte, gen.NoLocal, 32, 2, false, true}, 4, {}, true);
    });
    auto inlineData = gen.ArrayFromPlace({&fixed, 0, 0, 2, false, true}, {});
    assert(inlineData.layout.image == WasmCodeGen::ArrayImage::Inline);
    assert(inlineData.image.memory == 2 && inlineData.elementMemory == 2);
    TypeExpr growable(TY_ARRAY, {}); TypeArray growableDetail;
    growable.arr = &growableDetail; growableDetail.sub = byte; growableDetail.akind = A_GROW;
    bool refused = false;
    try { gen.ArrayFromPlace({&growable, 0, 0, 2, false, true}, {}); }
    catch (const CompileError &error) {
        refused = error.msg.find("growable array headers require a Memory 0 place") != string::npos;
    }
    assert(refused);
    refused = false;
    try { gen.EmitKnownOffset({byte, 0, 0, 2, true, true}, 1, {}); }
    catch (const CompileError &error) {
        refused = error.msg.find("array address is missing its concrete memory proof") != string::npos;
    }
    assert(refused);
    for (uint32_t i = 0; i < 3; i++) gen.module.exports.push_back({cat("memory", i), 2, i});
    auto bytes = gen.module.Finish();
    auto out = fopen(argv[1], "wb");
    if (!out) return 1;
    auto wrote = fwrite(bytes.data(), 1, bytes.size(), out);
    auto closed = fclose(out);
    return wrote == bytes.size() && !closed ? 0 : 1;
}
