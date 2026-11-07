// Backend-independent constraints for lexical data-stack call accounting.
#include "../src/data_stacks.h"
#include <cassert>
#include <stdexcept>

int main() {
    struct Function {} a, b, c, d;
    using Counts = goose::DataStackCounts<Function, int>;
    auto valid = [](Function *, const Counts::Call &) { assert(false); };
    {
        Counts plan;
        plan.own[&a] = 2;
        plan.own[&b] = 3;
        plan.own[&c] = 7;
        plan.own[nullptr] = 1;
        // b runs with both a's owners live. c runs after those owners have
        // left scope, so its bound is reused rather than added to theirs.
        plan.calls[&a] = {{&b, 2, 10}, {&c, 0, 11}};
        plan.calls[nullptr] = {{&a, 1, 12}};
        plan.Bound({&a, &b, &c}, valid);
        assert(plan.need[&a] == 7 && plan.need[nullptr] == 8);
    }
    {
        Counts plan;
        plan.own[&a] = 2;
        plan.own[&b] = 4;
        plan.own[&c] = 3;
        plan.own[&d] = 9;
        plan.calls[&a] = {{&b, 0, 20}};
        plan.calls[&b] = {{&a, 0, 21}, {&c, 4, 22}};
        // d is reachable from c but need not occur in the supplied roots.
        plan.calls[&c] = {{&d, 3, 23}};
        plan.Bound({&a}, valid);
        assert(plan.need[&c] == 12);
        assert(plan.need[&a] == 16 && plan.need[&b] == 16);
        assert(plan.need[nullptr] == 0);
    }
    {
        Counts plan;
        plan.calls[&a] = {{&b, 0, 30}};
        plan.calls[&b] = {{&a, 1, 31}};
        bool rejected = false;
        try {
            plan.Bound({&a, &b}, [&](Function *caller, const Counts::Call &edge) {
                assert(caller == &b && edge.callee == &a);
                assert(edge.offset == 1 && edge.line == 31);
                throw std::runtime_error("live stack across recursive edge");
            });
        } catch (const std::runtime_error &) { rejected = true; }
        assert(rejected);
    }
    {
        Counts plan;
        plan.own[&a] = 5;
        plan.calls[&a] = {{&a, 0, 40}};
        plan.Bound({&a}, valid);
        assert(plan.need[&a] == 5);
    }
}
