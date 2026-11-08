# Discarded fixed negation

Three native-valid parent cases fail Wasm compilation: array call, struct call, and a nested binary operand. Parent/compiler identity uses the fixed-binary candidate. No new binary result support is needed.

Change only Statement's existing fixed-binary discard dispatch to also accept root unary minus with FixedResult(ActualType(n)); use WithFixedTemporary and the current cleanup path. Keep general scalar statements unchanged. Run the three cases at both optimization levels in native, Node and Wasmtime, plus a loop's live frame tops and valid missing-restore control. No performance measurement under owner directive.
