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

// Private storage-plan controls. These are not source-language admission tests.
int main() {
    using namespace goose;
    Ast ast;
    WasmCodeGen gen(ast);
    auto scalar = ast.inttypes[IS_I64];
    TypeArray arrayInfo; arrayInfo.akind = A_FIXED; arrayInfo.sub = scalar; arrayInfo.size = 2;
    TypeExpr array(TY_ARRAY, {}); array.arr = &arrayInfo;
    TypeArray otherInfo = arrayInfo; otherInfo.size = 3;
    TypeExpr other(TY_ARRAY, {}); other.arr = &otherInfo;
    IntLit expression({}, 0), wrongExpression({}, 1);
    expression.exprtype = wrongExpression.exprtype = scalar;
    FnSpec otherFunction {};
    auto refused = [&](auto operation, const char *reason) {
        try { operation(); }
        catch (const CompileError &error) {
            assert(error.msg.find(reason) != string::npos);
            return;
        }
        assert(false && "missing storage-plan rejection");
    };
    bool constructed = false;
    auto reserve = [&] {
        gen.WithFixedValue(&array, &expression,
            [&](auto) { constructed = true; }, [](auto) {});
    };
    refused(reserve, "fixed temporary needs its symbolic storage plan");
    assert(!constructed && gen.scopes.empty());
    gen.storage.PlanTemporary(&expression, &other, nullptr);
    refused(reserve, "fixed temporary needs its symbolic storage plan");
    gen.storage.PlanTemporary(&expression, &array, &otherFunction);
    refused(reserve, "fixed temporary needs its symbolic storage plan");
    gen.storage.PlanTemporary(&expression, &array, nullptr);
    auto plan = gen.storage.Temporary(&expression, &array, nullptr);
    assert(plan && !gen.storage.Temporary(&wrongExpression, &array, nullptr));
    auto size = gen.storage.fixedtemporaries.at(&expression).size();
    gen.storage.PlanTemporary(&expression, &array, nullptr);
    assert(size == gen.storage.fixedtemporaries.at(&expression).size());

    Ident destination({}, "destination"); destination.exprtype = &array;
    Assign assignment({}, T_ASSIGN, &destination, &expression);
    assignment.exprtype = ast.voidtype;
    auto actual = [](Node *n, bool = false) { return n->exprtype; };
    int next = 0;
    gen.storage.Walk(&assignment, nullptr, next, actual);
    auto protection = gen.storage.Protection(&assignment, nullptr);
    assert(protection && protection->assignment == &assignment && protection->type == &array);
    assert(!gen.storage.Protection(&assignment, &otherFunction));
    auto assign = [&](TypeExpr *type, Node *rhs, TType op) {
        gen.AssignFixed({type, 0, 0, 0, false, true}, rhs, op, {});
    };
    refused([&] { assign(&array, &expression, T_ASSIGN); },
            "fixed assignment needs its planned protected destination");
    gen.protectedfixed = protection;
    refused([&] { assign(&other, &expression, T_ASSIGN); },
            "fixed assignment needs its planned protected destination");
    refused([&] { assign(&array, &wrongExpression, T_ASSIGN); },
            "fixed assignment needs its planned protected destination");
    refused([&] { assign(&array, &expression, T_PLUS); },
            "fixed assignment needs its planned protected destination");
    gen.current = &otherFunction;
    refused([&] { assign(&array, &expression, T_ASSIGN); },
            "fixed assignment needs its planned protected destination");
    gen.current = nullptr;
    // A compound scalar right operand still needs a destination-sized snapshot.
    Assign compound({}, T_MULEQ, &destination, &wrongExpression);
    compound.exprtype = ast.voidtype;
    gen.storage.Walk(&compound, nullptr, next, actual);
    assert(gen.storage.Temporary(&wrongExpression, &array, nullptr));
    // Reference rebinding has no pointee value commit.
    Assign rebind({}, T_DOTASSIGN, &destination, &expression);
    rebind.exprtype = ast.voidtype;
    gen.storage.Walk(&rebind, nullptr, next, actual);
    assert(!gen.storage.Protection(&rebind, nullptr));
}
