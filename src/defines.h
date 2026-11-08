// User C defines also provide literal constants in the build namespace.
#pragma once

namespace goose {

inline void AddDefine(Ast &ast, const string &definition) {
    auto equal = definition.find('=');
    auto name = definition.substr(0, equal);
    auto value = equal == string::npos ? string("1") : definition.substr(equal + 1);
    auto letter = [](char c) { return (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') || c == '_'; };
    // Function-like macros, C-only names and Goose keywords stay C-only.
    if (name.empty() || !letter(name[0]) || any_of(name.begin() + 1, name.end(), [&](char c) {
            return !letter(c) && !(c >= '0' && c <= '9');
        })) return;
    Lexer identifier("-D", name.c_str());
    if (identifier.tok != T_IDENT || value.empty()) return;
    Node *literal = nullptr;
    if (value == "true" || value == "false") {
        literal = ast.New<BoolLit>(Line {}, value == "true");
    } else if (value[0] == '"') {
        try {
            Lexer lex("-D", value.c_str());
            if (lex.tok != T_STRLIT || lex.smultiline || lex.p != value.c_str() + value.size()) return;
            literal = ast.New<StrLit>(Line {}, lex.sval);
        } catch (CompileError &) { return; }
    } else {
        auto negative = value[0] == '-';
        auto start = (negative || value[0] == '+') ? 1u : 0u;
        uint64_t magnitude = 0;
        auto first = value.data() + start, end = value.data() + value.size();
        auto result = from_chars(first, end, magnitude, 10);
        if (first == end || result.ec != errc {}) return;
        string suffix(result.ptr, size_t(end - result.ptr));
        for (auto &c : suffix) c = (char)tolower((unsigned char)c);
        uint64_t multiplier = 1;
        if (suffix == "k") multiplier <<= 10;
        else if (suffix == "m") multiplier <<= 20;
        else if (suffix == "g") multiplier <<= 30;
        else if (suffix == "t") multiplier <<= 40;
        else if (!suffix.empty() && suffix != "u" && suffix != "l" && suffix != "ll" &&
                 suffix != "ul" && suffix != "lu" && suffix != "ull" && suffix != "llu") return;
        if (magnitude > UINT64_MAX / multiplier) return;
        magnitude *= multiplier;
        if (negative && magnitude > (uint64_t(1) << 63)) return;
        // C suffixes do not narrow the Goose range or change signedness.
        auto bits = negative ? uint64_t(0) - magnitude : magnitude;
        auto uns = !negative && magnitude > uint64_t(INT64_MAX);
        auto integer = ast.New<IntLit>(Line {}, bit_cast<int64_t>(bits), string_view {}, uns);
        integer->fixedtype = ast.inttypes[uns ? IS_U64 : IS_I64];
        literal = integer;
    }
    if (ast.builddefinitions.count(name))
        throw CompileError { cat("-D ", definition, ": duplicate definition") };
    ast.builddefinitions.emplace(ast.Intern(name), literal);
}

inline void AddDefines(Ast &ast, const vector<string> &definitions) {
    for (auto &definition : definitions) AddDefine(ast, definition);
}

} // namespace goose
