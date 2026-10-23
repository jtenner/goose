// Specialization-time structural expansion. The generated trees use the
// ordinary checker, optimizer and code generator; no runtime iterator exists.
#pragma once

namespace goose {

// A body's trailing construct is a statement if any of its branches cannot
// supply a value. Arm fragments count only when their source is nonempty.
// This reads source shapes without checking or expanding expressions: a
// nested block's locals are not in scope yet, and its tail may be unreachable.
inline bool TypeCheck::IsValuelessTail(const Node *n) {
    size_t visited = 0;
    vector<pair<int, TypeExpr *>> bindings;
    function<TypeExpr *(TypeExpr *)> shape = [&](TypeExpr *t) -> TypeExpr * {
        set<TypeExpr *> seen;
        while (t && t->kind == TY_GENERIC) {
            if (!seen.insert(t).second) return nullptr;
            auto id = t->named->expansionbinding;
            if (!id) { t = LookupBindingOuter(t->named->name); continue; }
            auto found = find_if(bindings.rbegin(), bindings.rend(),
                                 [&](auto &b) { return b.first == id; });
            t = found == bindings.rend() ? nullptr : found->second;
        }
        if (t && t->kind == TY_VARIANT && !t->var->variant) {
            auto owner = shape(t->var->adt);
            auto v = owner && owner->kind == TY_ENUM ? owner->enu->en->FindVariant(t->var->name) : nullptr;
            return v ? ast.VariantTypeOf(owner, v, t->line) : nullptr;
        }
        return t;
    };
    function<bool(const Node *)> walk;
    auto arms = [&](const vector<MatchArm> &as) {
        return any_of(as.begin(), as.end(), [&](const MatchArm &a) {
            return walk(a.expansion ? a.expansion : a.body);
        });
    };
    walk = [&](const Node *x) {
        if (!x) return false;
        // Normal expansion diagnoses an oversized reachable source. The
        // shape walk must stay bounded even for a tail never reached.
        if (++visited > ExpansionClone::MAXNODES) return false;
        if (auto fi = Is<IfExpr>(x)) {
            if (fi->isconst) {
                // A source-shape walk runs before nested block scopes or
                // reachability exist. Selection belongs to CheckIf, where
                // locals shadow globals and unreachable tails are gone.
                return fi->selected && (!fi->thenb->tail || walk(fi->thenb));
            }
            return !fi->elseb || walk(fi->thenb) || walk(fi->elseb);
        }
        if (auto m = Is<MatchExpr>(x)) return arms(m->arms);
        if (auto cf = Is<ConstFor>(x)) {
            auto entry = [&](TypeExpr *t = nullptr) {
                if (t) bindings.push_back({ cf->bindings.back(), t });
                auto result = arms(cf->arms);
                if (t) bindings.pop_back();
                return result;
            };
            if (cf->source == ES_CONSTANTS) return !cf->constants.empty() && entry();
            if (cf->source == ES_TYPES) {
                for (auto t : cf->types) if (entry(shape(t))) return true;
                return false;
            }
            auto t = shape(cf->types[0]);
            if (!t) return false;
            if (cf->source == ES_FIELDS) {
                auto fields = t->kind == TY_STRUCT ? &t->struc->st->fields
                            : t->kind == TY_VARIANT ? &t->var->variant->fields : nullptr;
                return fields && any_of(fields->begin(), fields->end(),
                                        [](const Field &f) { return !f.ispad; }) && entry();
            }
            if (t->kind == TY_ENUM) {
                for (auto &v : t->enu->en->variants)
                    if (entry(ast.VariantTypeOf(t, &v, cf->line))) return true;
            }
            return false;
        }
        if (auto l = Is<LoopExpr>(x)) return !BreaksWithValue(l->body);
        if (auto b = Is<Block>(x)) return walk(b->tail);
        if (auto e = Is<EarlyBlock>(x)) return walk(e->body);
        return false;
    };
    return walk(n);
}

// A deliberately small evaluator: boolean structure plus the existing typed
// integer constant evaluator. Both operands are validated, even for && / ||;
// only bodies, never condition operands, are conditionally excluded.
inline bool TypeCheck::ConstBool(Node *n, set<VarDecl *> &visiting, ConstUse *use) {
    if (auto b = Is<BoolLit>(n)) return b->val;
    if (auto id = Is<Ident>(n)) {
        if (auto value = ast.LookupBuildDefinition(id->name, id->ns))
            return ConstBool(value, visiting, use);
        auto g = ast.LookupGlobal(id->name, id->ns);
        if (g && !g->isvar && g->inits.size() == 1 && (!g->type || g->type->kind == TY_BOOL)) {
            if (!visiting.insert(g).second) Error(n, "cycle in const if constant initializer");
            if (use && !g->defs.empty()) {
                if (!use->named) use->named = g->defs[0];
                RelyOnConstant(*use, g->defs[0]);
            }
            auto value = ConstBool(g->inits[0], visiting, use);
            visiting.erase(g);
            return value;
        }
    }
    if (auto u = Is<Unary>(n); u && u->op == T_NOT) return !ConstBool(u->child, visiting, use);
    if (auto b = Is<Binary>(n)) {
        if (b->op == T_ANDAND || b->op == T_OROR) {
            auto left = ConstBool(b->left, visiting, use);
            auto right = ConstBool(b->right, visiting, use);
            return b->op == T_ANDAND ? left && right : left || right;
        }
        switch (b->op) {
            case T_EQ: case T_NEQ: case T_LT: case T_LTEQ: case T_GT: case T_GTEQ: {
                Val l, r;
                bool llit, rlit;
                if (ConstIntValue(b->left, l, llit, visiting, use) &&
                    ConstIntValue(b->right, r, rlit, visiting, use)) {
                    auto lf = l, rf = r;
                    if (!llit) lf.ck = CK_NONE;
                    if (!rlit) rf.ck = CK_NONE;
                    lf.flexint = lf.flexint || lf.notconst;
                    rf.flexint = rf.flexint || rf.notconst;
                    lf.nonneg = !l.uns && l.ival >= 0;
                    rf.nonneg = !r.uns && r.ival >= 0;
                    auto t = UnifyNumeric(n, b->op, lf, rf, l.type, r.type, true);
                    if (l.notconst) l.ival = WrapStorage(l.ival, t->intstorage);
                    if (r.notconst) r.ival = WrapStorage(r.ival, t->intstorage);
                    auto uns = IsUnsigned(t->intstorage);
                    auto cmp = uns ? ((uint64_t)l.ival < (uint64_t)r.ival ? -1 : l.ival == r.ival ? 0 : 1)
                                   : (l.ival < r.ival ? -1 : l.ival == r.ival ? 0 : 1);
                    switch (b->op) {
                        case T_EQ: return cmp == 0;
                        case T_NEQ: return cmp != 0;
                        case T_LT: return cmp < 0;
                        case T_LTEQ: return cmp <= 0;
                        case T_GT: return cmp > 0;
                        case T_GTEQ: return cmp >= 0;
                        default: break;
                    }
                }
                if (b->op == T_EQ || b->op == T_NEQ) {
                    function<optional<string_view>(Node *)> stringconstant = [&](Node *x) -> optional<string_view> {
                        if (auto str = Is<StrLit>(x)) return str->val;
                        if (auto id = Is<Ident>(x)) {
                            if (auto value = ast.LookupBuildDefinition(id->name, id->ns)) return stringconstant(value);
                            auto g = ast.LookupGlobal(id->name, id->ns);
                            if (g && !g->isvar && g->inits.size() == 1 &&
                                (!g->type || (g->type->kind == TY_SLICE && IsU8(g->type->sub)))) {
                                if (!visiting.insert(g).second) Error(x, "cycle in const if string constant");
                                if (use && !g->defs.empty()) {
                                    if (!use->named) use->named = g->defs[0];
                                    RelyOnConstant(*use, g->defs[0]);
                                }
                                auto value = stringconstant(g->inits[0]);
                                visiting.erase(g);
                                return value;
                            }
                        }
                        return nullopt;
                    };
                    auto ls = stringconstant(b->left), rs = stringconstant(b->right);
                    if (ls && rs) return b->op == T_EQ ? *ls == *rs : *ls != *rs;
                    auto left = ConstBool(b->left, visiting, use);
                    auto right = ConstBool(b->right, visiting, use);
                    return b->op == T_EQ ? left == right : left != right;
                }
                break;
            }
            default: break;
        }
    }
    // Build-definition literals have no source location. Diagnose their
    // condition use (also through aliases) without changing the shared value.
    auto at = !n->line.line && use && use->at ? use->at : n;
    Error(at, "const if requires a bool constant expression (literals, global constants, build definitions, !, &&, || and comparisons)");
}

inline bool TypeCheck::ConstIfCondition(Node *condition) {
    ConstNames(condition, "const if condition");
    ConstUse use { condition, "const if condition" };
    set<VarDecl *> visiting;
    auto result = ConstBool(condition, visiting, &use);
    if (ast.exemplars) {
        // These names are compile-time uses. Retain checked bindings for
        // navigation without putting the discarded condition in runtime ASTs.
        function<void(Node *)> bind = [&](Node *n) {
            if (auto id = Is<Ident>(n)) {
                auto global = ast.LookupGlobal(id->name, id->ns);
                if (global && !global->defs.empty()) id->vdef = global->defs[0];
            }
            n->Children(bind);
        };
        bind(condition);
        ast.constantconditions.push_back(condition);
    }
    return result;
}

inline void SelectConditionalFields(Ast &ast) {
    auto conditional = [](const vector<Field> &fields) {
        return any_of(fields.begin(), fields.end(), [](const Field &f) { return f.condition; });
    };
    auto needed = any_of(ast.structs.begin(), ast.structs.end(), [&](SStruct *s) { return conditional(s->fields); }) ||
                  any_of(ast.enums.begin(), ast.enums.end(), [&](SEnum *e) {
                      return any_of(e->variants.begin(), e->variants.end(), [&](const SVariant &v) { return conditional(v.fields); });
                  });
    if (!needed) return;
    // Keep global VarDefs stable: the ordinary checker reuses these so its
    // later writes still diagnose assumptions used for layout selection.
    TypeCheck tc(ast, false, true, true);
    auto flatten = [&](vector<Field> &fields, vector<Field> &written,
                       const vector<GenericParam> &generics) {
        if (none_of(fields.begin(), fields.end(), [](const Field &f) { return f.condition; })) return;
        written = fields;
        vector<Field> flat;
        function<void(const vector<Field> &)> append = [&](const vector<Field> &fs) {
            for (auto &f : fs) {
                if (f.condition) {
                    tc.ConstExprNames(f.condition, "const if field condition", [&](Ident *id, const char *) {
                        for (auto &g : generics)
                            if (g.name == id->name)
                                tc.Error(id, "const if field condition names a type parameter; type-dependent field conditions are unsupported");
                    });
                    auto take = tc.ConstIfCondition(f.condition);
                    append(take ? f.thenfields : f.elsefields);
                } else {
                    ResolveConditionalBody(ast, f.defaultval, f.type);
                    for (auto &prev : flat)
                        if (!f.ispad && !prev.ispad && f.name == prev.name)
                            tc.Error(f.line, cat("duplicate field name: ", f.name));
                    flat.push_back(f);
                }
            }
        };
        append(fields);
        fields = std::move(flat);
    };
    for (auto st : ast.structs) {
        tc.CheckRoot([&] { flatten(st->fields, st->declfields, st->generics); });
        // On a failed selection retain the source, but expose no marker as
        // a real field to the recovery checker.
        erase_if(st->fields, [](const Field &f) { return f.condition != nullptr; });
    }
    for (auto en : ast.enums) for (auto &v : en->variants) {
        tc.CheckRoot([&] { flatten(v.fields, v.declfields, en->generics); });
        erase_if(v.fields, [](const Field &f) { return f.condition != nullptr; });
    }
}

inline void TypeCheck::SelectConstIf(IfExpr *x) {
    if (x->selected) return;
    auto take = ConstIfCondition(x->cond);
    Node *body = take ? (Node *)x->thenb : x->elseb;
    auto chosen = Is<Block>(body);
    if (!chosen) {
        chosen = ast.New<Block>(x->line);
        // Else-if chains are const-if expressions in their own scope.
        if (body) chosen->tail = body;
    }
    ResolveConditionalBody(ast, chosen);
    ResolvePools();
    ResolveIndexTypes();
    x->thenb = chosen;
    x->elseb = nullptr;
    x->cond = ast.New<BoolLit>(x->cond->line, true);
    x->cond->exprtype = ast.booltype;
    x->selected = true;
}

inline Node *TypeCheck::ExpansionConstant(Node *n, set<VarDecl *> &visiting) {
    if (auto id = Is<Ident>(n))
        if (auto value = ast.LookupBuildDefinition(id->name, id->ns))
            return value->Clone(ast);
    // Checking a named global may have inserted its ordinary integer-to-
    // float conversion. This is not permission for a source-level cast.
    if (auto a = Is<AsCast>(n); a && a->implicit) {
        auto c = ExpansionConstant(a->child, visiting);
        if (auto i = Is<IntLit>(c)) {
            auto f = ast.New<FltLit>(n->line, i->uns ? (double)(uint64_t)i->val : (double)i->val);
            f->fixedtype = a->type;
            if (a->type->fltstorage == FS_F32) f->val = (float)f->val;
            return f;
        }
        Error(n, "unsupported conversion in const for constant source");
    }
    Val v;
    bool literal;
    set<VarDecl *> integers;
    ConstUse use { n, "const for source" };
    if (ConstIntValue(n, v, literal, integers, &use)) {
        // `~c` (Val::notconst) stays one, to adapt where the entry is used.
        if (v.notconst)
            return ast.New<Unary>(n->line, T_BITNOT, ast.New<IntLit>(n->line, v.litlo));
        auto i = ast.New<IntLit>(n->line, v.ival, string_view {}, v.uns);
        // An unannotated named literal keeps its ordinary adaptability.
        // Arithmetic still follows ConstIntValue's evaluation widths.
        if (auto id = Is<Ident>(n)) {
            auto g = ast.LookupGlobal(id->name, id->ns);
            if (g && !g->type && g->defs[0]->constlit) literal = true;
        }
        if (!literal) i->fixedtype = v.type;
        return i;
    }
    if (Is<StrLit>(n) || Is<BoolLit>(n) || Is<FltLit>(n)) return n->Clone(ast);
    if (auto u = Is<Unary>(n); u && u->op == T_MINUS) {
        if (auto f = Is<FltLit>(u->child)) return ast.New<FltLit>(n->line, -f->val);
    }
    if (auto id = Is<Ident>(n)) {
        auto g = ast.LookupGlobal(id->name, id->ns);
        if (g && !g->isvar && g->inits.size() == 1) {
            if (!visiting.insert(g).second) Error(n, "cycle in const for constant initializer");
            use.named = g->defs[0];
            RelyOnConstant(use, g->defs[0]);
            auto c = ExpansionConstant(g->inits[0], visiting);
            visiting.erase(g);
            auto t = g->defs[0]->type ? g->defs[0]->type : g->type;
            if (t && t->kind == TY_FLT) {
                if (auto i = Is<IntLit>(c))
                    c = ast.New<FltLit>(n->line, i->uns ? (double)(uint64_t)i->val : (double)i->val);
                auto f = Is<FltLit>(c);
                if (!f) Error(n, "const for named floating constant requires a numeric constant initializer");
                if (g->type || !g->defs[0]->constlit) f->fixedtype = ast.PlainOf(t);
                if (t->fltstorage == FS_F32) f->val = (float)f->val;
                return c;
            }
            if (Is<FltLit>(c) && !t) return c;
            if (Is<BoolLit>(c) && (!t || t->kind == TY_BOOL)) return c;
            if (Is<StrLit>(c) && (!t || (t->kind == TY_SLICE && IsU8(t->sub)))) return c;
        }
    }
    Error(n, "const for source requires a scalar or string constant, or supported integer constant expression");
}

inline void TypeCheck::ExpandConstFor(ConstFor *cf, const function<void(ExpansionClone &)> &emit) {
    // Resolve the complete source before creating any fragment instances.
    vector<vector<ExpansionArg>> entries;
    vector<string> descriptions;
    if (cf->source == ES_CONSTANTS) {
        for (size_t i = 0; i < cf->constants.size(); i++) {
            auto n = cf->constants[i];
            ConstNames(n, "const for source");
            set<VarDecl *> visiting;
            auto value = ExpansionConstant(n, visiting);
            entries.push_back({ { cf->bindings[0], value } });
            descriptions.push_back(cat("constant entry ", i + 1, " (", ExprStr(n), ")"));
        }
    } else {
        vector<TypeExpr *> types;
        for (auto raw : cf->types) {
            ConstNamesIn(raw);
            auto t = Subst(raw);
            if (HasGenerics(t)) Error(cf, cat("const for source requires a concrete type, got ", TypeStr(t)));
            if (cf->source == ES_FIELDS && t->kind != TY_STRUCT && t->kind != TY_VARIANT)
                Error(cf, cat("fields requires a concrete struct or variant type, got ", TypeStr(t)));
            if (cf->source == ES_VARIANTS && ast.PlainOf(t)->kind != TY_ENUM)
                Error(cf, cat("variants requires a concrete ADT type, got ", TypeStr(t)));
            if (t->kind != TY_FN) ValidateType(t, cf->line, VT_POINTEE);
            types.push_back(t);
        }
        if (cf->source == ES_FIELDS) {
            // A variant type's payload is a struct-like run of fields (§3.5),
            // reached as a struct's are, on a value of that variant type.
            auto t = ast.PlainOf(types[0]);
            auto &fields = t->kind == TY_VARIANT ? t->var->variant->fields : GetStructInst(t)->st->fields;
            for (auto &f : fields) {
                if (f.ispad) continue;
                entries.push_back({ { cf->bindings[0], ast.New<StrLit>(cf->line, string(f.name)) },
                                    { cf->bindings[1], nullptr, nullptr, t, f.name } });
                descriptions.push_back(cat("field ", TypeStr(t), ".", f.name));
            }
        } else if (cf->source == ES_VARIANTS) {
            // Every variant in declaration order: its name, and the variant as
            // a type, a pattern, a constructor and, payload-less, a value.
            auto t = ast.PlainOf(types[0]);
            for (auto &v : t->enu->en->variants) {
                auto vt = ast.VariantTypeOf(t, &v, cf->line);
                Node *value = nullptr;
                if (none_of(v.fields.begin(), v.fields.end(), [](const Field &f) { return !f.ispad; }))
                    value = ast.New<StructLit>(cf->line, vt);
                ExpansionArg variant { cf->bindings[1], value, vt };
                variant.variant = v.name;
                entries.push_back({ { cf->bindings[0], ast.New<StrLit>(cf->line, string(v.name)) }, variant });
                descriptions.push_back(cat("variant ", TypeStr(t), ".", v.name));
            }
        } else {
            for (auto t : types) {
                entries.push_back({ { cf->bindings[0], nullptr, t } });
                descriptions.push_back(cat("type ", TypeStr(t)));
            }
        }
    }
    for (size_t i = 0; i < entries.size(); i++) {
        ExpansionClone ctx;
        ctx.args = std::move(entries[i]);
        ctx.trace = ast.Intern(cat("\n  in const for ", descriptions[i], " at ", Where(cf->line),
                                  cf->expansiontrace));
        ctx.size = &expansionsize;
        ctx.error = [&](Line line, const string &msg) {
            ErrorIn(LocOf(line), msg, Chain(ctx.trace));
        };
        auto saved = ast.expansionclone;
        ast.expansionclone = &ctx;
        // Cloning is the only operation using this context. Recursive
        // expansion and ordinary checking take place after it is restored.
        try { emit(ctx); } catch (...) { ast.expansionclone = saved; throw; }
        ast.expansionclone = saved;
    }
}

inline Block *TypeCheck::ExpandStatements(ConstFor *cf) {
    auto out = ast.New<Block>(cf->line);
    out->origin = cf->Origin();
    out->expansiontrace = cf->expansiontrace;
    ExpandConstFor(cf, [&](ExpansionClone &) {
        auto body = (Block *)cf->body->Clone(ast);
        body->expansionboundary = true;
        out->stmts.push_back(body);
    });
    return out;
}

// A match's arm list with each `const for` of arms replaced by its arms, one
// set per entry, in place: the ordinary match checks then see every arm.
inline void TypeCheck::ExpandArms(vector<MatchArm> &arms) {
    if (none_of(arms.begin(), arms.end(), [](const MatchArm &a) { return a.expansion != nullptr; }))
        return;
    vector<MatchArm> flat;
    for (auto &arm : arms) {
        if (auto cf = Is<ConstFor>(arm.expansion)) {
            vector<MatchArm> generated;
            ExpandConstFor(cf, [&](ExpansionClone &) {
                for (auto &a : cf->arms) {
                    generated.push_back(CloneArm(ast, a));
                    generated.back().generated = true;
                }
            });
            ExpandArms(generated);
            flat.insert(flat.end(), generated.begin(), generated.end());
        } else {
            flat.push_back(arm);
        }
    }
    arms = std::move(flat);
}

inline void TypeCheck::ExpandInitializers(vector<FieldInit> &inits) {
    if (none_of(inits.begin(), inits.end(), [](const FieldInit &fi) { return Is<ConstFor>(fi.val) || Is<ConstInitIf>(fi.val); }))
        return;
    vector<FieldInit> flat;
    for (auto &fi : inits) {
        if (auto ci = Is<ConstInitIf>(fi.val)) {
            auto take = ConstIfCondition(ci->cond);
            auto selected = ci->branches[take ? 0 : 1];
            for (auto &entry : selected) ResolveConditionalBody(ast, entry.val);
                    ResolvePools();
            ResolveIndexTypes();
            ExpandInitializers(selected);
            flat.insert(flat.end(), selected.begin(), selected.end());
        } else if (auto cf = Is<ConstFor>(fi.val)) {
            vector<FieldInit> generated;
            ExpandConstFor(cf, [&](ExpansionClone &) {
                for (auto &entry : cf->inits) generated.push_back(ast.CloneFieldInit(entry));
            });
            ExpandInitializers(generated);
            flat.insert(flat.end(), generated.begin(), generated.end());
        } else {
            flat.push_back(fi);
        }
    }
    inits = std::move(flat);
}

} // namespace goose
