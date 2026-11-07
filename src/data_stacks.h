// Shared data-stack accounting. Call offsets come from lexical storage
// lifetimes, independently of a backend's representation of stack addresses.
#pragma once

#include <algorithm>
#include <cstdint>
#include <functional>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace goose {

template<class Function, class Location> struct DataStackCounts {
    struct Call {
        Function *callee;
        int offset;
        Location line;
    };
    std::unordered_map<Function *, std::vector<Call>> calls;
    std::unordered_map<Function *, int> own;
    std::unordered_map<Function *, int64_t> need;

    // A function hands its first free stack to each callee. Recursive
    // components share one bound: an edge within a cycle must have offset 0
    // (Goose section 7.8). Visit components callees first so outside bounds
    // are final. nullptr represents global initializers and render helpers.
    template<class InvalidCycle>
    void Bound(const std::vector<Function *> &functions, InvalidCycle invalid) {
        std::unordered_map<Function *, int> index, low;
        std::vector<Function *> stack;
        std::unordered_set<Function *> onstack;
        int next = 0;
        std::function<void(Function *)> visit = [&](Function *v) {
            index[v] = low[v] = next++;
            stack.push_back(v);
            onstack.insert(v);
            if (auto it = calls.find(v); it != calls.end()) {
                for (auto &c : it->second) {
                    auto w = c.callee;
                    if (!index.count(w)) {
                        visit(w);
                        low[v] = std::min(low[v], low[w]);
                    } else if (onstack.count(w)) {
                        low[v] = std::min(low[v], index[w]);
                    }
                }
            }
            if (low[v] != index[v]) return;
            std::vector<Function *> scc;
            for (;;) {
                auto w = stack.back();
                stack.pop_back();
                onstack.erase(w);
                scc.push_back(w);
                if (w == v) break;
            }
            std::unordered_set<Function *> members(scc.begin(), scc.end());
            int64_t count = 0;
            for (auto m : scc) {
                count = std::max(count, (int64_t)own[m]);
                auto it = calls.find(m);
                if (it == calls.end()) continue;
                for (auto &c : it->second) {
                    if (members.count(c.callee)) {
                        if (c.offset) invalid(m, c);
                        continue;
                    }
                    count = std::max(count, c.offset + need[c.callee]);
                }
            }
            for (auto m : scc) need[m] = count;
        };
        for (auto f : functions) if (!index.count(f)) visit(f);
        if (!index.count(nullptr)) visit(nullptr);
    }
};

}  // namespace goose
