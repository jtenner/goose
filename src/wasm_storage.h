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
    enum class FixedOrigin { Declaration, MatchCopy, IterationCopy, Parameter, CallbackParameter };
    struct FixedOwner {
        uint32_t bytes = 0, image = 0;
        Node *initialization = nullptr;
        FixedOrigin origin = FixedOrigin::Declaration;
        FnSpec *function = nullptr;
        bool argument = false, initialized = false;
    };
    unordered_map<VarDef *, FixedOwner> fixedvalues;
    // Symbolic sites precede frame binding. One expression may need several
    // stored types, for example a fixed source copied into a limited parameter.
    struct FixedTemporary {
        TypeExpr *type;
        FnSpec *function;
    };
    unordered_map<Node *, vector<FixedTemporary>> fixedtemporaries;
    struct ProtectedDestination {
        Assign *assignment;
        TypeExpr *type;
        FnSpec *function;
    };
    unordered_map<Assign *, vector<ProtectedDestination>> protectedvalues;

    void PlanTemporary(Node *expression, TypeExpr *type, FnSpec *function) {
        if (!expression || !type) return;
        while (type->kind == TY_REF) type = type->ref->sub;
        if (!FixedParameter(type)) return;
        auto &sites = fixedtemporaries[expression];
        if (none_of(sites.begin(), sites.end(), [&](const FixedTemporary &site) {
                return site.function == function && layout.TEq(site.type, type);
            })) sites.push_back({type, function});
    }

    const FixedTemporary *Temporary(Node *expression, TypeExpr *type, FnSpec *function) const {
        auto it = fixedtemporaries.find(expression);
        if (it != fixedtemporaries.end())
            for (auto &site : it->second)
                if (site.function == function && layout.TEq(site.type, type)) return &site;
        return nullptr;
    }

    const ProtectedDestination *Protection(Assign *assignment, FnSpec *function) const {
        auto it = protectedvalues.find(assignment);
        if (it != protectedvalues.end())
            for (auto &site : it->second) if (site.function == function) return &site;
        return nullptr;
    }
    unordered_set<TypeExpr *> notedtypes;
    // -1 is dynamic, a missing entry is not yet reached. A concrete base is
    // valid only when every incoming call agrees on it.
    unordered_map<FnSpec *, int> bases;
    uint32_t localmemories = 0;
    bool dataaddresses = false;
    bool byteprints = false;

    explicit WasmStoragePlan(Ast &a, ValueLayout &l) : ast(a), layout(l) {}

    void NoteType(TypeExpr *type) {
        if (!type || dataaddresses || notedtypes.count(type)) return;
        vector<TypeExpr *> work {type};
        while (!work.empty()) {
            auto t = work.back(); work.pop_back();
            if (!notedtypes.insert(t).second) continue;
            if (t->kind == TY_REF) work.push_back(t->ref->sub);
            else if (t->kind == TY_ARRAY) {
                if (Owns(t)) { dataaddresses = true; return; }
                work.push_back(t->arr->sub);
            } else if (t->kind == TY_STRUCT) {
                for (auto ft : layout.SI(t)->ftypes) if (ft) work.push_back(ft);
            } else if (t->kind == TY_ENUM) {
                for (auto &types : layout.EIOf(t)->vftypes)
                    for (auto ft : types) if (ft) work.push_back(ft);
            } else if (t->kind == TY_VARIANT) {
                auto ei = layout.EIVar(t);
                for (auto ft : ei->vftypes[ei->en->VariantIndex(t->var->variant)])
                    if (ft) work.push_back(ft);
            }
        }
    }

    // Owners admitted by the current array lowering. Other compound classes
    // are rejected before emission until their destination plan is complete.
    bool Owns(TypeExpr *t) {
        return t && t->kind == TY_ARRAY && (layout.IsResz(t) || t->arr->akind == A_VAR ||
               (t->arr->akind == A_LIMITED && layout.ArrSize(t->arr) < 0));
    }

    bool FixedParameter(TypeExpr *t) {
        return WasmValueSupport::Nominal(t) || (t && t->kind == TY_ARRAY &&
               (t->arr->akind == A_FIXED ||
                (t->arr->akind == A_LIMITED && layout.ArrSize(t->arr) >= 0)));
    }

    template<class ActualType> void Walk(Node *n, FnSpec *function, int &next, ActualType &actual) {
        if (!n || Is<FnDecl>(n)) return;
        NoteType(n->exprtype);
        PlanTemporary(n, actual(n), function);
        if (auto assignment = Is<Assign>(n); assignment && assignment->op != T_DOTASSIGN) {
            auto type = actual(assignment->lval);
            if (type && assignment->pointee && type->kind == TY_REF) type = type->ref->sub;
            if (FixedParameter(type)) {
                auto &sites = protectedvalues[assignment];
                if (none_of(sites.begin(), sites.end(), [&](const ProtectedDestination &site) {
                        return site.function == function;
                    })) sites.push_back({assignment, type, function});
                // Compound operations can retain the old destination while a
                // scalar or aggregate right operand runs. Its stored type is
                // the destination type, not necessarily the operand's type.
                PlanTemporary(assignment->rhs, type, function);
            }
        }
        if (auto b = Is<Block>(n)) {
            auto saved = next;
            vector<Defer *> deferred;
            for (auto statement : b->stmts) {
                if (auto d = Is<Defer>(statement)) deferred.push_back(d);
                else Walk(statement, function, next, actual);
            }
            Walk(b->tail, function, next, actual);
            // A deferred body can be emitted at several exits. Give it one
            // conservative index above all owners in its registering block,
            // so every emitted copy uses the same safe allocation/call plan.
            for (auto it = deferred.rbegin(); it != deferred.rend(); ++it)
                Walk((*it)->body, function, next, actual);
            next = saved;
            return;
        }
        if (auto d = Is<Defer>(n)) { Walk(d->body, function, next, actual); return; }
        if (auto v = Is<VarDecl>(n)) {
            for (size_t i = 0; i < v->defs.size(); i++) {
                auto d = v->defs[i];
                NoteType(d->type);
                if (WasmValueSupport::Nominal(d->type) || (v->inline_arg && FixedParameter(d->type))) {
                    auto &fixed = fixedvalues[d];
                    fixed.initialization = v;
                    fixed.argument = v->inline_arg;
                    fixed.initialized = i < v->inits.size();
                }
                if (!Owns(d->type)) continue;
                if (i < v->inits.size()) {
                    auto source = v->inits[i];
                    while (auto call = Is<Call>(source)) {
                        if (call->builtin != B_COPY) break;
                        source = call->ValueArgNodes().at(0);
                    }
                    // A nonfixed receiver can materialize a fixed source whose
                    // outer expression already has the receiving array type.
                    PlanTemporary(source, actual(source, true), function);
                }
                if (d->isglobal) {
                    if (owners.emplace(d, 0).second) globals.push_back(d);
                } else {
                    owners[d] = (uint32_t)next++;
                    counts.own[function] = std::max(counts.own[function], next);
                }
            }
            for (auto init : v->inits) Walk(init, function, next, actual);
            return;
        }
        if (auto loop = Is<ForLoop>(n); loop && WasmValueSupport::Nominal(loop->vdef->type)) {
            if (loop->iterkind == IK_ARRAY && !loop->byref && loop->vdef->copybind) {
                NoteType(loop->vdef->type);
                FixedOwner fixed;
                fixed.initialization = loop;
                fixed.origin = FixedOrigin::IterationCopy;
                fixed.initialized = true;
                fixedvalues[loop->vdef] = fixed;
            }
            Walk(loop->iter, function, next, actual);
            Walk(loop->body, function, next, actual);
            return;
        }
        if (auto match = Is<MatchExpr>(n)) {
            Walk(match->scrutinee, function, next, actual);
            auto incoming = next;
            for (auto &arm : match->arms) {
                next = incoming;
                if (arm.binder && WasmValueSupport::Nominal(arm.binder->type)) {
                    NoteType(arm.binder->type);
                    auto &fixed = fixedvalues[arm.binder];
                    fixed.initialization = match;
                    fixed.origin = FixedOrigin::MatchCopy;
                    fixed.initialized = true;
                }
                Walk(arm.body, function, next, actual);
            }
            next = incoming;
            return;
        }
        if (auto c = Is<Call>(n)) {
            if (c->defaultinit) { Walk(c->defaultinit, function, next, actual); return; }
            size_t argumentCount = 0;
            for (auto argument : c->ValueArgNodes()) {
                argumentCount++;
                if (c->builtin == B_PRINT) {
                    auto t = argument->exprtype;
                    while (t && t->kind == TY_REF) t = t->ref->sub;
                    if (t && t->kind == TY_ARRAY && t->arr->sub->kind == TY_INT &&
                        t->arr->sub->intstorage == IS_U8) byteprints = true;
                }
                auto &parameters = c->spec ? c->spec->params : c->fvparams;
                if (argumentCount <= parameters.size())
                    PlanTemporary(argument, parameters[argumentCount - 1]->type, function);
                Walk(argument, function, next, actual);
            }
            if (c->fvbody) {
                for (size_t i = 0; i < c->fvparams.size(); i++) {
                    auto parameter = c->fvparams[i];
                    if (!FixedParameter(parameter->type)) continue;
                    NoteType(parameter->type);
                    FixedOwner fixed;
                    fixed.initialization = c;
                    fixed.origin = FixedOrigin::CallbackParameter;
                    fixed.function = function;
                    fixed.argument = true;
                    fixed.initialized = i < argumentCount;
                    fixedvalues[parameter] = fixed;
                }
                Walk(c->fvbody, function, next, actual); return;
            }
            if (c->builtin < 0 && c->spec) {
                calltops[c] = next;
                counts.calls[function].push_back({c->spec, next, c->line});
            }
            return;
        }
        n->Children([&](Node *child) { Walk(child, function, next, actual); });
    }

    template<class Fail, class FixedSize, class ActualType>
    void Build(Fail fail, FixedSize fixedsize, ActualType actual) {
        vector<FnSpec *> functions;
        for (auto sp : ast.fnspecs) if (sp->live) {
            functions.push_back(sp);
            for (auto p : sp->params) {
                NoteType(p->type);
                if (FixedParameter(p->type)) {
                    FixedOwner fixed;
                    fixed.origin = FixedOrigin::Parameter;
                    fixed.function = sp;
                    fixed.argument = fixed.initialized = true;
                    fixedvalues[p] = fixed;
                }
            }
            for (auto t : sp->rets) NoteType(t);
            int next = 0;
            Walk(sp->body, sp, next, actual);
        }
        for (auto declaration : ast.globals) {
            int next = 0;
            Walk(declaration, nullptr, next, actual);
        }
        for (auto &[owner, plan] : fixedvalues) {
            if (plan.argument && plan.origin == FixedOrigin::Declaration) {
                auto declaration = Is<VarDecl>(plan.initialization);
                if (!declaration || !declaration->inline_arg)
                    fail(owner->line, "aggregate argument needs its checked inline declaration");
            }
            if (!plan.initialized) fail(owner->line, "uninitialized aggregate declarations need the pending destination lowering");
            if (owner->reusable) fail(owner->line, "pool owners need the pending descriptor lowering");
            plan.image = fixedsize(owner->type, owner->line);

            plan.bytes = std::max(1u, plan.image);
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
