/* Test-only raw aliases to live ordinary Goose scalar objects. */
#include <stdint.h>
#include <string.h>
static int64_t *unsafe_alias_saved;
static void *unsafe_alias_capture(int64_t *p) { unsafe_alias_saved = p; return p; }
static void unsafe_alias_external_store(void *p, int64_t value) { memcpy(p, &value, sizeof value); }
static void unsafe_alias_saved_store(int64_t value) { memcpy(unsafe_alias_saved, &value, sizeof value); }
static void unsafe_alias_handle_store(uint64_t p, int64_t value) { memcpy((void *)(uintptr_t)p, &value, sizeof value); }
static int64_t unsafe_alias_pair(int64_t x, int64_t y) { return x * 10 + y; }
