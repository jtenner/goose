// Closed scalar compile-time calls. Arithmetic remains in the existing evaluators.
#pragma once
namespace goose {

inline TypeExpr *TypeCheck::ConstScalar(TypeExpr *t, Line at) {
    if (!t || t->cq || t->aliasuse || t->ix ||
        !(t->kind == TY_BOOL || (t->kind == TY_INT && t->intstorage == IS_U64)))
        Error(at, "const fn requires literal bool or u64 types");
    return t;
}

inline Node *TypeCheck::ConstBody(SFunction *sf) {
    auto b = sf->body;
    auto r = b && b->stmts.size() == 1 ? Is<Return>(b->stmts[0]) : nullptr;
    if (!r || b->tail || r->vals.size() != 1 || !r->from.empty())
        Error(sf->line, "const fn body requires exactly one return expression");
    return r->vals[0];
}

inline SFunction *TypeCheck::ConstCallee(Call *c, bool body) {
    auto id = Is<Ident>(c->callee);
    if (!id || !c->tyargs.empty() || c->trailing)
        Error(c, "const fn requires a direct scalar call without type arguments");
    if (!body) ConstName(id, "constant callee");
    if (body && constfunction)
        for (auto &p : constfunction->params)
            if (p.name == id->name) Error(c, "const fn parameter is not callable");
    auto &fs = ast.LookupFunctions(id->name, id->ns);
    if (fs.size() != 1 || !fs[0]->isconstfn)
        Error(c, "constant call requires a unique const fn");
    auto sf = fs[0];
    if (sf->params.size() != c->args.size()) Error(c, "const fn argument count mismatch");
    return sf;
}

inline TypeExpr *TypeCheck::ConstKind(Node *n) {
    if (Is<BoolLit>(n)) return ast.booltype;
    if (auto i = Is<IntLit>(n)) {
        if (!i->uns && i->val < 0) Error(n, "const fn integer literal must fit u64");
        return ast.inttypes[IS_U64];
    }
    if (auto id = Is<Ident>(n)) {
        for (auto &p : constfunction->params)
            if (p.name == id->name) return ConstScalar(p.type, p.line);
        Error(n, "const fn body cannot read free names");
    }
    if (auto b = Is<Block>(n)) {
        if (!b->stmts.empty() || !b->tail) Error(n, "const fn branch requires one expression");
        return ConstKind(b->tail);
    }
    if (auto x = Is<IfExpr>(n)) {
        if (x->isconst || !x->elseb) Error(n, "const fn requires expression if with both arms");
        auto c = ConstKind(x->cond), l = ConstKind(x->thenb), r = ConstKind(x->elseb);
        if (c != ast.booltype || l != r) Error(n, "const fn if scalar kind mismatch");
        return l;
    }
    if (auto c = Is<Call>(n)) {
        auto sf = ConstCallee(c, true);
        for (size_t i = 0; i < c->args.size(); i++)
            if (ConstKind(c->args[i]) != ConstScalar(sf->params[i].type, sf->line))
                Error(c->args[i], "const fn argument scalar kind mismatch");
        if (sf->rets.size() != 1) Error(c, "const fn requires one result");
        return ConstScalar(sf->rets[0], sf->line);
    }
    if (auto u = Is<Unary>(n)) {
        auto t = ConstKind(u->child);
        if ((u->op == T_NOT && t == ast.booltype) ||
            (u->op == T_BITNOT && t == ast.inttypes[IS_U64])) return t;
        Error(n, "unsupported const fn unary operator or scalar kind");
    }
    if (auto b = Is<Binary>(n)) {
        auto l = ConstKind(b->left), r = ConstKind(b->right);
        if (l != r) Error(n, "const fn operator scalar kind mismatch");
        switch (b->op) {
            case T_ANDAND: case T_OROR:
                if (l == ast.booltype) return l;
                break;
            case T_EQ: case T_NEQ: return ast.booltype;
            case T_LT: case T_LTEQ: case T_GT: case T_GTEQ:
                if (l == ast.inttypes[IS_U64]) return ast.booltype;
                break;
            case T_PLUS: case T_MINUS: case T_MUL: case T_DIV: case T_MOD:
            case T_BITAND: case T_BITOR: case T_XOR: case T_SHL: case T_SHR:
                if (l == ast.inttypes[IS_U64]) return l;
                break;
            default: break;
        }
        Error(n, "unsupported const fn binary operator or scalar kind");
    }
    Error(n, "unsupported expression in const fn");
}

inline void TypeCheck::CheckConstFunctions() {
    for (auto sf : ast.functions) {
        if (!sf->isconstfn) continue;
        CheckRoot([&] {
            if (sf->isnested || sf->isextern || sf->isexport || sf->isbench || sf->issimd ||
                sf->isinline || sf->isthread || sf->isrec || sf->checkfree || !sf->generics.empty())
                Error(sf->line, "const fn requires an unmodified top-level nongeneric declaration");
            if (ast.LookupFunctions(sf->name, sf->ns).size() != 1)
                Error(sf->line, "const fn cannot be overloaded");
            if (sf->params.size() > 16) Error(sf->line, "const fn parameter limit is 16");
            for (auto &p : sf->params) {
                ConstScalar(p.type, p.line);
                if (p.isvar || p.defaultval) Error(p.line, "const fn forbids parameter modifiers and defaults");
            }
            if (sf->rets.size() != 1) Error(sf->line, "const fn requires one explicit result");
            Saved<SFunction *> context(constfunction, sf);
            if (ConstKind(ConstBody(sf)) != ConstScalar(sf->rets[0], sf->line))
                Error(sf->line, "const fn return scalar kind mismatch");
        });
    }
}

inline Node *TypeCheck::ConstBranch(IfExpr *x, set<VarDecl *> &visiting, ConstUse *use) {
    auto b = ConstBool(x->cond, visiting, use) ? (Node *)x->thenb : x->elseb;
    if (!b) Error(x, "constant expression if requires else");
    return b;
}

inline Val TypeCheck::ConstCall(Call *c, set<VarDecl *> &visiting, ConstUse *use) {
    auto sites = constsites;
    if (sites.empty() && use && use->at) sites.push_back(use->at);
    sites.push_back(c);
    Saved<decltype(constsites)> request(constsites, std::move(sites));
    auto sf = ConstCallee(c, constfunction != nullptr);
    vector<pair<string_view, Val>> args;
    for (size_t i = 0; i < c->args.size(); i++) {
        auto n = c->args[i];
        Val v;
        auto t = ConstScalar(sf->params[i].type, sf->params[i].line);
        if (t->kind == TY_BOOL) {
            v.type = ast.booltype;
            v.ival = ConstBool(n, visiting, use);
        } else {
            bool literal;
            if (!ConstIntValue(n, v, literal, visiting, use) || v.notconst ||
                !FitsIntStorage(v.ival, v.uns, IS_U64)) Error(n, "const fn argument must fit u64");
            v.type = ast.inttypes[IS_U64];
            v.uns = v.ival < 0;
            v.constfrom = nullptr;
        }
        args.push_back({sf->params[i].name, v});
    }
    if (constcalls.size() >= 32) Error(c, "const fn active call limit is 32");
    for (auto &entry : constcalls)
        if (entry.first == sf) Error(c, "active const fn call cycle");
    auto calls = constcalls;
    calls.push_back({sf, c});
    Saved<decltype(constcalls)> trace(constcalls, std::move(calls));
    Saved<decltype(constargs)> bindings(constargs, std::move(args));
    Saved<SFunction *> context(constfunction, sf);
    auto body = ConstBody(sf);
    Val v;
    if (sf->rets.size() != 1) Error(c, "const fn requires one result");
    auto t = ConstScalar(sf->rets[0], sf->line);
    if (t->kind == TY_BOOL) {
        v.type = t;
        v.ival = ConstBool(body, visiting, use);
    } else {
        bool literal;
        if (!ConstIntValue(body, v, literal, visiting, use)) Error(body, "const fn result requires u64");
    }
    return v;
}

inline void TypeCheck::NormalizeConstGlobal(VarDecl *g) {
    bool contains = false;
    function<void(Node *)> find = [&](Node *n) {
        if (auto c = Is<Call>(n)) {
            if (auto id = Is<Ident>(c->callee))
                for (auto sf : ast.LookupFunctions(id->name, id->ns)) contains |= sf->isconstfn;
        }
        n->Children(find);
    };
    for (auto n : g->inits) find(n);
    if (!contains) return;
    if (!g->isconst || g->inits.size() != 1 || g->names.size() != 1)
        Error(g, "const fn global initializer requires one typed scalar const");
    auto t = ConstScalar(g->type, g->line);
    auto n = g->inits[0];
    ConstNames(n, "const fn global initializer");
    ConstUse use {g, "const fn global initializer"};
    set<VarDecl *> visiting {g};
    Node *result;
    if (t->kind == TY_BOOL) result = ast.New<BoolLit>(n->line, ConstBool(n, visiting, &use));
    else {
        Val v;
        bool literal;
        if (!ConstIntValue(n, v, literal, visiting, &use) || v.notconst ||
            !FitsIntStorage(v.ival, v.uns, IS_U64)) Error(n, "const fn global result must fit u64");
        auto i = ast.New<IntLit>(n->line, v.ival, string_view {}, v.ival < 0);
        i->fixedtype = ast.inttypes[IS_U64];
        result = i;
    }
    g->sourceinits = g->inits;
    g->inits = {result};
}

} // namespace goose
