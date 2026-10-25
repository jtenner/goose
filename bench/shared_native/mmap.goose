// Same 64 map/close operations as baseline.c's mmap case. No page touching.
// Size variants intentionally do the same work. Python supplies the stable file.
import os;

bench "Map and close a prepared file" fn mmap_lifecycle() -> u64 {
    var checksum: u64 = 0;
    for i in 64 {
        let mapped, ok = shared_map_readonly(build::BENCH_FIXTURE, 16777216);
        assert(ok);
        checksum += shared_size(mapped);
        assert(shared_close(mapped));
    }
    checksum
}
