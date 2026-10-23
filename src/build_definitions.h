// Native compiler configuration: typed literal symbols, independent of C -D.
#pragma once

namespace goose {

inline void AddBuildDefinition(Ast &ast, const string &definition) {
    auto fail = [&](const string &why) -> void {
        throw CompileError { cat("--define ", definition, ": ", why) };
    };
    auto equal = definition.find('=');
    if (equal == string::npos || equal == 0 || equal + 1 == definition.size())
        fail("expected NAME=VALUE with an explicit value");
    auto name = definition.substr(0, equal);
    auto value = definition.substr(equal + 1);
    auto letter = [](char c) { return (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') || c == '_'; };
    if (!letter(name[0]) || any_of(name.begin() + 1, name.end(), [&](char c) {
            return !letter(c) && !(c >= '0' && c <= '9');
        })) fail("invalid identifier");
    Lexer identifier("--define", name.c_str());
    if (identifier.tok != T_IDENT) fail("identifier is a reserved keyword");
    if (ast.builddefinitions.count(name)) fail("duplicate definition");
    Node *literal = nullptr;
    if (value == "true" || value == "false") {
        literal = ast.New<BoolLit>(Line {}, value == "true");
    } else if (value[0] == '"') {
        try {
            Lexer lex("--define", value.c_str());
            if (lex.tok != T_STRLIT || lex.smultiline) fail("expected a string literal");
            literal = ast.New<StrLit>(Line {}, lex.sval);
            // No trailing comments, whitespace, or another expression.
            if (lex.p != value.c_str() + value.size()) fail("trailing text after string literal");
        } catch (CompileError &) { fail("invalid string literal"); }
    } else {
        auto negative = value[0] == '-';
        auto start = (negative || value[0] == '+') ? 1u : 0u;
        uint64_t magnitude = 0;
        auto first = value.data() + start, end = value.data() + value.size();
        auto result = from_chars(first, end, magnitude, 10);
        if (first == end || result.ec == errc::invalid_argument || result.ptr != end)
            fail("expected true, false, a decimal integer, or a string literal");
        if (result.ec == errc::result_out_of_range || (negative && magnitude > (uint64_t(1) << 63)))
            fail("integer overflow (supported range: -2^63 through 2^64-1)");
        // Bit casting avoids implementation-defined out-of-range signed conversion.
        auto bits = negative ? uint64_t(0) - magnitude : magnitude;
        auto uns = !negative && magnitude > uint64_t(INT64_MAX);
        auto integer = ast.New<IntLit>(Line {}, bit_cast<int64_t>(bits), string_view {}, uns);
        integer->fixedtype = ast.inttypes[uns ? IS_U64 : IS_I64];
        literal = integer;
    }
    ast.builddefinitions.emplace(ast.Intern(name), literal);
}

inline void AddBuildDefinitions(Ast &ast, const vector<string> &definitions) {
    for (auto &definition : definitions) AddBuildDefinition(ast, definition);
}

} // namespace goose
