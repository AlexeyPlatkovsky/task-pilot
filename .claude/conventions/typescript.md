# TypeScript Standard

- Keep strict typing; prefer concrete types, generics, or `unknown` over `any`.
- Model domain, transport, persistence, and UI types at their boundaries.
- Prefer small pure functions for parsing, validation, graph operations, and serialization.
- Return structured domain errors instead of parsing human-readable messages.
- Inject filesystem, clock, and identifier dependencies when determinism requires it.
- Serialize with stable field order, normalized timestamps, and explicit newline behavior.
- Add abstractions only after at least two real call sites require the same behavior.
