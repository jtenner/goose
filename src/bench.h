// Native transport and parent-owned thermal supervision.
#pragma once
#include "bench_thermal.h"
#include "bench_report.h"
namespace goose {
struct BenchProgram { string executable, key, size, directory; };
int RunBenchmarks(const vector<BenchProgram> &programs, bool fresh, int warmups, int samples, const BenchThermalOptions &thermal, BenchThermalSource *source = nullptr, BenchReport *report = nullptr);
string BenchDirectory();
// Compiled as its own translation unit, without LTO. No workload code is
// visible to this timer, so every release performs exactly one opaque call.
inline const char *BenchRunnerSource() { return R"C(
#define _GNU_SOURCE
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <sys/resource.h>
extern void gs_bench_init(int, char **);
extern int gs_bench_lookup(const char *, void (**)(void), int (**)(FILE *));
static uint64_t now(void) {
    struct timespec t;
    if (clock_gettime(CLOCK_MONOTONIC, &t)) _exit(120);
    return (uint64_t)t.tv_sec * 1000000000 + t.tv_nsec;
}
int gs_bench_runner(int argc, char **argv) {
    if (argc != 3) return 121;
    int fd = atoi(argv[2]);
    FILE *control = fdopen(fd, "w");
    FILE *commands = fdopen(dup(fd), "r");
    if (!control || !commands) return 122;
    setvbuf(control, NULL, _IONBF, 0);
    void (*call)(void) = NULL;
    int (*result)(FILE *) = NULL;
    if (!gs_bench_lookup(argv[1], &call, &result)) return 123;
    gs_bench_init(argc, argv);
    fprintf(control, "READY\n");
    for (;;) {
        int command = fgetc(commands);
        if (command == 'Q') return 0;
        if (command != 'C') return 124;
        __asm__ __volatile__("" ::: "memory");
        uint64_t start = now();
        __asm__ __volatile__("" ::: "memory");
        call();
        __asm__ __volatile__("" ::: "memory");
        uint64_t end = now();
        __asm__ __volatile__("" ::: "memory");
        // Encoding and observable checksum consumption are outside the clock.
        char *checksum = NULL;
        size_t length = 0;
        FILE *sink = open_memstream(&checksum, &length);
        if (!sink) return 125;
        int finite = result(sink);
        fclose(sink);
        struct rusage usage;
        if (getrusage(RUSAGE_SELF, &usage)) return 126;
        fprintf(control, "%llu %llu %d %llu %s\n", (unsigned long long)start,
                (unsigned long long)end, finite, (unsigned long long)usage.ru_maxrss * 1024, checksum);
        free(checksum);
    }
}
)C"; }
}
