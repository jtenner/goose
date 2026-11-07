// Symbolic storage assignment for checked Wasm functions. No instructions or
// C source are emitted here. Logical indices follow lexical lifetimes; a
// later binding maps them to physical Wasm memories.
#pragma once

namespace goose {

struct WasmStoragePlan {
    Ast &ast;
    ValueLayout &layout;
    DataStackCounts<FnSpec, Line> counts;
    unordered_map<VarDef *, uint32_t> owners;
    unordered_map<Call *, int> calltops;
    vector<VarDef *> globals;
    // -1 is dynamic, a missing entry is not yet reached. A concrete base is
    // valid only when every incoming call agrees on it.
    unordered_map<FnSpec *, int> bases;
    uint32_t localmemories = 0;
    bool dataaddresses = false;
    bool byteprints = false;

    explicit WasmStoragePlan(Ast &a, ValueLayout &l) : ast(a), layout(l) {}

    void NoteType(TypeExpr *type) {
        if (dataaddresses) return;
        while (type) {
            if (type->kind == TY_REF) { type = type->ref->sub; continue; }
            if (type->kind != TY_ARRAY) return;
            if (layout.IsResz(type) || type->arr->akind == A_VAR) { dataaddresses = true; return; }
            type = type->arr->sub;
        }
    }

    // Owners admitted by the current array lowering. Other compound classes
    // are rejected before emission until their destination plan is complete.
    bool Owns(TypeExpr *t) {
        return t && t->kind == TY_ARRAY && (layout.IsResz(t) || t->arr->akind == A_VAR);
    }

    void Walk(Node *n, FnSpec *function, int &next) {
        if (!n || Is<FnDecl>(n)) return;
        NoteType(n->exprtype);
        if (auto b = Is<Block>(n)) {
            auto saved = next;
            vector<Defer *> deferred;
            for (auto statement : b->stmts) {
                if (auto d = Is<Defer>(statement)) deferred.push_back(d);
                else Walk(statement, function, next);
            }
            Walk(b->tail, function, next);
            // A deferred body can be emitted at several exits. Give it one
            // conservative index above all owners in its registering block,
            // so every emitted copy uses the same safe allocation/call plan.
            for (auto it = deferred.rbegin(); it != deferred.rend(); ++it)
                Walk((*it)->body, function, next);
            next = saved;
            return;
        }
        if (auto d = Is<Defer>(n)) { Walk(d->body, function, next); return; }
        if (auto v = Is<VarDecl>(n)) {
            for (auto d : v->defs) {
                NoteType(d->type);
                if (!Owns(d->type)) continue;
                if (d->isglobal) {
                    if (owners.emplace(d, 0).second) globals.push_back(d);
                } else {
                    owners[d] = (uint32_t)next++;
                    counts.own[function] = std::max(counts.own[function], next);
                }
            }
            for (auto init : v->inits) Walk(init, function, next);
            return;
        }
        if (auto c = Is<Call>(n)) {
            if (c->defaultinit) { Walk(c->defaultinit, function, next); return; }
            for (auto argument : c->ValueArgNodes()) {
                if (c->builtin == B_PRINT) {
                    auto t = argument->exprtype;
                    while (t && t->kind == TY_REF) t = t->ref->sub;
                    if (t && t->kind == TY_ARRAY && t->arr->sub->kind == TY_INT &&
                        t->arr->sub->intstorage == IS_U8) byteprints = true;
                }
                Walk(argument, function, next);
            }
            if (c->fvbody) { Walk(c->fvbody, function, next); return; }
            if (c->builtin < 0 && c->spec) {
                calltops[c] = next;
                counts.calls[function].push_back({c->spec, next, c->line});
            }
            return;
        }
        n->Children([&](Node *child) { Walk(child, function, next); });
    }

    template<class Fail> void Build(Fail fail) {
        vector<FnSpec *> functions;
        for (auto sp : ast.fnspecs) if (sp->live) {
            functions.push_back(sp);
            for (auto p : sp->params) NoteType(p->type);
            for (auto t : sp->rets) NoteType(t);
            int next = 0;
            Walk(sp->body, sp, next);
        }
        for (auto declaration : ast.globals) {
            int next = 0;
            Walk(declaration, nullptr, next);
        }
        counts.Bound(functions, [&](FnSpec *caller, const auto &edge) {
            fail(edge.line, cat("live data stack across recursive call from ", caller->sf->name,
                                " to ", edge.callee->sf->name));
        });
        auto need = counts.need[nullptr];
        auto main = ast.MainFunction();
        auto entry = main && !main->specs.empty() ? main->specs[0] : nullptr;
        if (entry) need = std::max(need, counts.need[entry]);
        if (need > 64 || globals.size() > 64 - (uint64_t)need)
            fail(main ? main->line : Line {}, "this program exceeds the Wasm backend's 64 data-memory limit");
        localmemories = (uint32_t)need;
        for (size_t i = 0; i < globals.size(); i++)
            owners[globals[i]] = localmemories + (uint32_t)i;

        // Each function enters this queue at most twice: one known base,
        // then a conflict. Thus propagation is bounded by the call graph,
        // rather than enumerating combinations of incoming identities.
        vector<FnSpec *> work;
        auto meet = [&](FnSpec *to, int base) {
            auto [it, fresh] = bases.emplace(to, base);
            if (fresh) work.push_back(to);
            else if (it->second >= 0 && it->second != base) {
                it->second = -1;
                work.push_back(to);
            }
        };
        meet(nullptr, 0);
        if (entry) meet(entry, 0);
        for (size_t i = 0; i < work.size(); i++) {
            auto from = work[i];
            auto base = bases.at(from);
            if (auto it = counts.calls.find(from); it != counts.calls.end())
                for (auto &edge : it->second)
                    meet(edge.callee, base < 0 ? -1 : base + edge.offset);
        }
    }

    uint32_t Memories() const { return 1 + localmemories + (uint32_t)globals.size(); }
    int Base(FnSpec *function) const {
        auto it = bases.find(function);
        return it == bases.end() ? -1 : it->second;
    }
    int Memory(VarDef *owner, FnSpec *function) const {
        auto index = owners.at(owner);
        if (owner->isglobal) return 1 + (int)index;
        auto base = Base(function);
        return base < 0 ? -1 : 1 + base + (int)index;
    }
};

}  // namespace goose
