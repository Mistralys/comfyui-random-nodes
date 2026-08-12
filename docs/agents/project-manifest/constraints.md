# Constraints & Conventions

## Project Philosophy

Each node is designed to fill a single, well-defined role and to be **stable by design**. Nodes are not expected to evolve once built — the only exceptions are bug fixes and adaptations required by ComfyUI API changes. Feature creep, scope expansion, and speculative enhancements are explicitly out of scope.

## Non-Negotiable Design Decisions

These require explicit user approval to change.

- **V3 API only** — no V1 compatibility layer.
- **No external dependencies** — stdlib (`random`, `math`, etc.) and ComfyUI builtins only.

## Behavioral Invariants

- **Randomization control** — each node exposes a socketless `randomized` boolean input. `True` generates a new random value on execution; `False` returns the stored `value` widget value unchanged. There is no seed input.
- **Conditional caching via `fingerprint_inputs`** — each node's `fingerprint_inputs()` returns `time.time()` when `randomized=True` (forces re-execution every run) and a deterministic fingerprint derived from `value` when `randomized=False` (allows ComfyUI to cache the result). `not_idempotent=True` is not used, since these nodes are only conditionally non-reproducible.
- **Equal ranges permitted** — `range_from == range_to` is a valid input and returns the single possible value; it is not rejected by `validate_inputs`.

## Project Conventions

- **Reference patterns:** Follow `skill_test_nodes/` in the companion workspace (`comfyui-custom-node-skills/skill_test_nodes/`) for V3 API usage patterns.
- **Node ID prefix:** `Mistralys_` — all node IDs use this author prefix (e.g. `Mistralys_RandomInt`).
- **Node category:** `random` — all nodes use this flat category string.
- **Testing strategy — two tiers:**
  - **Unit tests (mock-based):** Standalone Python scripts that mock ComfyUI internals. Run without a live ComfyUI instance. Use `verify_*.py` naming; place in the `tests/` subdirectory.
  - **Manual integration tests:** Nodes must also be tested inside a live ComfyUI instance to validate UI rendering, widget behaviour, and actual output values. Unit tests cannot replace this layer.
- **Test coverage expectation:** Every new node should ship with a corresponding `verify_*.py` script covering its acceptance criteria.
- **Changelog:** Maintain `changelog.md` at the project root. Add an entry for every meaningful change.
