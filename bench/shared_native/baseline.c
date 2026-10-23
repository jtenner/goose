/* Benchmark-only original-style native helper baseline. No Goose application
 * imports this file. Pointer/range handles are weaker than native capabilities. */
#define _POSIX_C_SOURCE 200809L
#include <assert.h>
#include <fcntl.h>
#include <inttypes.h>
#include <pthread.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>
#ifndef CHECK_REGISTER_CLOBBERS
#define CHECK_REGISTER_CLOBBERS 0
#endif
static _Atomic uint64_t next_job, slots[8];
static uint8_t data[1048576];
static uint64_t n;
static int mode;
struct args { uint64_t index; };
static double now(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return t.tv_sec + t.tv_nsec * 1e-9; }
static uint64_t read64(size_t off) { assert(off <= sizeof(data) - 8); uint64_t v; memcpy(&v, data + off, 8); return v; }
static void write64(size_t off, uint64_t v) { assert(off <= sizeof(data) - 8); memcpy(data + off, &v, 8); }
static void *atomic_worker(void *opaque) {
    struct args *a = opaque;
    if (mode == 2) { while (atomic_fetch_add_explicit(&next_job, 1, memory_order_relaxed) < n) {} }
    else for (uint64_t i = 0; i < n; i++) atomic_fetch_add_explicit(&slots[mode == 0 ? a->index : 0], 1, memory_order_relaxed);
    return NULL;
}
static void *empty(void *opaque) { (void)opaque; return NULL; }
static void *producer(void *opaque) {
    (void)opaque;
    for (uint64_t i = 0; i < n; i++) {
        while (atomic_load_explicit(&next_job, memory_order_acquire) != 0) {}
        write64(0, i + 1); atomic_store_explicit(&next_job, 1, memory_order_release);
    }
    return NULL;
}
static void *consumer(void *opaque) {
    (void)opaque;
    for (uint64_t i = 0; i < n; i++) {
        while (atomic_load_explicit(&next_job, memory_order_acquire) != 1) {}
        assert(read64(0) == i + 1); atomic_store_explicit(&next_job, 0, memory_order_release);
    }
    return NULL;
}
struct check_state {
    uint64_t value;
#if CHECK_REGISTER_CLOBBERS
    uint64_t register_owners[2];
#endif
};
static void checked_emit(struct check_state *s, uint64_t v) {
#if CHECK_REGISTER_CLOBBERS
    assert(s->register_owners[0] == 0); s->register_owners[0] = v + 1;
#endif
    s->value += v;
#if CHECK_REGISTER_CLOBBERS
    assert(s->register_owners[0] == v + 1); s->register_owners[0] = 0;
#endif
}
int main(int argc, char **argv) {
    assert(argc == 5); n = strtoull(argv[2], NULL, 10); uint64_t workers = strtoull(argv[3], NULL, 10);
    assert(n > 0 && workers >= 1 && workers <= 8); const char *which = argv[1];
    uint64_t operations = n, checksum = 0; pthread_t threads[8]; struct args args[8];
    const double start = now();
    if (!strcmp(which,"atomics_uncontended") || !strcmp(which,"atomics_contended") || !strcmp(which,"claims")) {
        mode = !strcmp(which,"claims") ? 2 : !strcmp(which,"atomics_uncontended") ? 0 : 1;
        for (uint64_t w = 0; w < workers; w++) { args[w].index = w; assert(!pthread_create(&threads[w],NULL,atomic_worker,&args[w])); }
        for (uint64_t w = 0; w < workers; w++) assert(!pthread_join(threads[w],NULL));
        operations = mode == 2 ? n : n * workers; checksum = mode == 2 ? next_job : slots[0];
    } else if (!strcmp(which,"publication")) {
        if (n > 10000) n = 10000;
        operations = n;
        assert(!pthread_create(&threads[0],NULL,producer,NULL)); assert(!pthread_create(&threads[1],NULL,consumer,NULL));
        assert(!pthread_join(threads[0],NULL)); assert(!pthread_join(threads[1],NULL)); checksum = n;
    } else if (!strcmp(which,"scheduling")) {
        uint64_t rounds = n / 1000; if (!rounds) rounds = 1; operations = rounds * workers;
        for (uint64_t r = 0; r < rounds; r++) {
            for (uint64_t w = 0; w < workers; w++) assert(!pthread_create(&threads[w],NULL,empty,NULL));
            for (uint64_t w = 0; w < workers; w++) assert(!pthread_join(threads[w],NULL));
        }
        checksum = operations;
    } else if (!strcmp(which,"mmap")) {
        operations = 64;
        for (uint64_t i = 0; i < operations; i++) {
            int fd = open(argv[4],O_RDONLY); assert(fd >= 0); struct stat st;
            assert(!fstat(fd,&st) && st.st_size >= 16777216);
            void *p = mmap(NULL,16777216,PROT_READ,MAP_PRIVATE,fd,0); close(fd);
            assert(p != MAP_FAILED); checksum += 16777216; assert(!munmap(p,16777216));
        }
    } else if (!strcmp(which,"copy")) {
        uint64_t loops = n / 512; if (!loops) loops = 1;
        for (uint64_t i = 0; i < loops; i++) { memmove(data + 524288,data,524288); atomic_signal_fence(memory_order_seq_cst); }
        operations = loops * 524288; checksum = read64(524288);
    } else if (!strcmp(which,"checks_disabled") || !strcmp(which,"checks_enabled")) {
        struct check_state s = {0}; for (uint64_t i = 0; i < n; i++) checked_emit(&s,i & 65535); checksum = s.value;
    } else {
        for (uint64_t i = 0; i < 8192; i++) write64(i * 8,(i + 1) % 8192);
        if (!strcmp(which,"scalar_read_latency")) { for (uint64_t i = 0; i < n; i++) checksum = read64(checksum * 8); }
        else if (!strcmp(which,"scalar_write_latency")) { for (uint64_t i = 0; i < n; i++) { write64(0,checksum + 1); checksum = read64(0); atomic_signal_fence(memory_order_seq_cst); } }
        else if (!strcmp(which,"scalar_read_throughput")) {
            for (uint64_t i = 0; i < n; i++) { uint64_t off=(i&2047)*8; checksum += read64(off)+read64(off+16384)+read64(off+32768)+read64(off+49152); atomic_signal_fence(memory_order_seq_cst); } operations=n*4;
        } else { assert(!strcmp(which,"scalar_write_throughput"));
            for (uint64_t i=0;i<n;i++) { uint64_t off=(i&2047)*8; write64(off,i); write64(off+16384,i); write64(off+32768,i); write64(off+49152,i); atomic_signal_fence(memory_order_seq_cst); } operations=n*4; checksum=read64(((n-1)&2047)*8);
        }
    }
    printf("%.9f %" PRIu64 " %" PRIu64 "\n",now()-start,operations,checksum);
    return 0;
}
