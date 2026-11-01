// Source/checked initializer separation through the real compiler pipeline.
#include <fstream>
#define main goose_original_main
#include "../src/main.cpp"
#undef main

using namespace goose;
int main(int argc, char **argv) {
    if (argc != 3) return 2;
    const string path = argv[2];
    for (int input : {1, 7, 1}) for (int delta : {1, 2}) {
        auto text = cat("const fn helper(n:u64)->u64{return n+", delta,
                        ";}\nconst X:u64=helper(build::INPUT);\nfn main(){}\n");
        { ofstream f(path); f << text; }
        Ast ast;
        AddBuildDefinitions(ast, {cat("INPUT=", input)});
        ParseProgram(ast, path, {argv[1]}, DirOf(argv[0]));
        ResolveTypeNames(ast);
        if (!ast.errors.empty()) return 3;
        auto g = ast.LookupGlobal("X", "");
        auto source = g->inits[0];
        string before;
        source->Dump(before, 0);
        TypeCheckProgram(ast);
        if (!ast.errors.empty() || g->sourceinits.size() != 1 || g->sourceinits[0] != source) return 4;
        auto value = Is<IntLit>(g->inits[0]);
        if (!value || value->fixedtype != ast.inttypes[IS_U64] || value->val != input + delta) return 5;
        string after, declaration;
        source->Dump(after, 0);
        g->Dump(declaration, 0);
        if (before != after || declaration.find(before) == string::npos) return 6;
        auto clone = Is<VarDecl>(g->Clone(ast));
        if (!clone || !Is<Call>(clone->inits[0]) || !clone->sourceinits.empty()) return 7;
    }
    remove(path.c_str());
    puts("const fn source retention: 6 fresh configurations and helper edits passed");
}
