// Portable compiler-side unsigned 128-bit constants. No host __int128 required.
#pragma once
#include <cstdint>
#include <string>
#include <string_view>
#include <utility>

namespace goose {
struct UInt128 {
    uint64_t lo = 0, hi = 0;
    constexpr UInt128(uint64_t l = 0, uint64_t h = 0) : lo(l), hi(h) {}
    constexpr bool operator==(const UInt128 &) const = default;
    constexpr bool operator<(UInt128 b) const { return hi != b.hi ? hi < b.hi : lo < b.lo; }
    constexpr bool operator>(UInt128 b) const { return b < *this; }
    constexpr bool operator<=(UInt128 b) const { return !(b < *this); }
    constexpr explicit operator bool() const { return lo || hi; }
    constexpr UInt128 operator~() const { return {~lo, ~hi}; }
    constexpr UInt128 operator+(UInt128 b) const {
        auto l = lo + b.lo; return {l, hi + b.hi + (l < lo)};
    }
    constexpr UInt128 operator-(UInt128 b) const { return {lo - b.lo, hi - b.hi - (lo < b.lo)}; }
    constexpr UInt128 operator&(UInt128 b) const { return {lo & b.lo, hi & b.hi}; }
    constexpr UInt128 operator|(UInt128 b) const { return {lo | b.lo, hi | b.hi}; }
    constexpr UInt128 operator^(UInt128 b) const { return {lo ^ b.lo, hi ^ b.hi}; }
    // These are mathematical shifts. Goose's masked shift counts are applied
    // by the evaluator before calling them; internal algorithms need >=128=0.
    constexpr UInt128 operator<<(unsigned n) const {
        if (n >= 128) return {};
        if (!n) return *this;
        if (n >= 64) return {0, lo << (n - 64)};
        return {lo << n, (hi << n) | (lo >> (64 - n))};
    }
    constexpr UInt128 operator>>(unsigned n) const {
        if (n >= 128) return {};
        if (!n) return *this;
        if (n >= 64) return {hi >> (n - 64), 0};
        return {(lo >> n) | (hi << (64 - n)), hi >> n};
    }
    UInt128 operator*(UInt128 b) const {
        UInt128 r, a = *this;
        while (b) {
            if (b.lo & 1) r = r + a;
            a = a << 1; b = b >> 1;
        }
        return r;
    }
    std::pair<UInt128, UInt128> DivRem(UInt128 b) const {
        // Caller rejects zero. Bitwise long division retains the carry from
        // the 129th remainder bit, including divisors above 2^127.
        UInt128 q, r;
        for (int i = 127; i >= 0; --i) {
            bool carry = r.hi >> 63;
            r = (r << 1) | ((*this >> i) & UInt128(1));
            if (carry || !(r < b)) { r = r - b; q = q | (UInt128(1) << i); }
        }
        return {q, r};
    }
    UInt128 operator/(UInt128 b) const { return DivRem(b).first; }
    UInt128 operator%(UInt128 b) const { return DivRem(b).second; }
    static bool Parse(std::string_view text, unsigned base, UInt128 &out) {
        if (text.empty() || (base != 10 && base != 16)) return false;
        UInt128 v, max = ~UInt128();
        auto [limit, remainder] = max.DivRem(base);
        for (auto c : text) {
            unsigned d = c >= '0' && c <= '9' ? c - '0'
                       : c >= 'a' && c <= 'f' ? c - 'a' + 10
                       : c >= 'A' && c <= 'F' ? c - 'A' + 10 : 255;
            if (d >= base || limit < v || (v == limit && d > remainder.lo)) return false;
            v = v * base + d;
        }
        out = v; return true;
    }
    std::string Decimal() const {
        if (!*this) return "0";
        std::string out;
        auto n = *this;
        while (n) {
            auto [q, r] = n.DivRem(10);
            out.insert(out.begin(), char('0' + r.lo)); n = q;
        }
        return out;
    }
    double ToDouble() const { return (double)hi * 18446744073709551616.0 + (double)lo; }
};
} // namespace goose
