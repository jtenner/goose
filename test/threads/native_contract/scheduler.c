#include <stdint.h>
#include <stdlib.h>
#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#endif
/* No Goose pointer escapes. These scalar handles index this one fixture's
   sealed state, not a general safe-handle implementation. */
static int64_t next_job;
static int64_t jobs[128], results[128];
static int alive;
static void valid(uint64_t handle) { if (handle != 1 || !alive) abort(); }
uint64_t contract_create(void) {
    alive = 1; next_job = 0;
    for (int i = 0; i < 128; ++i) { jobs[i] = i * 3; results[i] = -1; }
    return 1;
}
int64_t contract_snapshot(uint64_t handle) { valid(handle); return 128; }
int64_t contract_claim(uint64_t handle) {
    valid(handle);
#ifdef _WIN32
    return InterlockedExchangeAdd64((volatile LONG64 *)&next_job, 1);
#else
    return __atomic_fetch_add(&next_job, 1, __ATOMIC_RELAXED);
#endif
}
int64_t contract_job(uint64_t handle, int64_t index) { valid(handle); return jobs[index]; }
void contract_report(uint64_t handle, int64_t index, int64_t value) {
    valid(handle); results[index] = value;
}
int64_t contract_result(uint64_t handle, int64_t index) { valid(handle); return results[index]; }
void contract_destroy(uint64_t handle) { valid(handle); alive = 0; }
