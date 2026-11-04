#include <stdint.h>

uint64_t mod64(uint32_t *p) { return (uint64_t)(uintptr_t)p & 63u; }
