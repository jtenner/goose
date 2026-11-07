// ArrayBuffer views can change or detach while a guest runs.
export function snapshotMemory(memory) {
    return Buffer.from(new Uint8Array(memory.buffer));
}
