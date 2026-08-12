# Plan

## Plan Audit Cycles
- Audits: 1 — Plan Auditor v1.7.0
- Architectural Reviews: 2 — Plan Architect Reviewer v2.2.0

## Summary

Implement two ComfyUI V3 custom nodes — **Random Int** and **Random Float** — that generate random numbers within user-defined ranges. Each node features socketless widget inputs (`value`, `randomized`) that control whether a new random number is generated or a stored value is reused, plus frontend buttons ("New random value", "Use current: {N}") for interactive value management. The implementation includes a JavaScript frontend extension for button behavior and widget synchronization, unit tests, packaging, and full documentation updates.

## Architectural Context

The `comfyui-random-nodes` project is a pre-implementation V3-only custom node package. The project manifest, constraints, and file tree are established but no source code exists yet. The sibling project `comfyui-json-nodes` provides a proven reference implementation for V3 node structure, extension registration, packaging, and testing patterns. The companion workspace `comfyui-custom-node-skills` provides authoritative V3 API documentation.

Key established conventions:
- **Author prefix**: `Mistralys_` — all node IDs prefixed (e.g., `Mistralys_RandomInt`)
- **Node category**: `random` — flat category, no hierarchy
- **Extension class**: `RandomNodesExtension` in `__init__.py`
- **Node definitions**: all node classes in `nodes.py`
- **Frontend code**: `js/random_nodes.js` loaded via `WEB_DIRECTORY = "./js"`

## Approach / Architecture

### Backend Architecture (nodes.py)

Two node classes share a common pattern: socket inputs define the generation range, socketless inputs (`value`, `randomized`) control behavior, and outputs pass through both the result and the range parameters.

**Execution flow:**
1. If `randomized` is `True`: generate a random number within the range (applying step/precision constraints for floats), return it as the output, and include the generated value via `ui.PreviewText` for frontend widget synchronization (also displays the value on the node).
2. If `randomized` is `False`: return the `value` widget value directly as the output.

**Caching strategy:**
Each node implements `fingerprint_inputs()` for conditional cache control:
- When `randomized` is `True`: return `time.time()` to force re-execution every run.
- When `randomized` is `False`: return a deterministic fingerprint based on the `value` input, allowing ComfyUI to cache the result.

This is preferred over `not_idempotent=True` because these nodes are only conditionally non-reproducible.

**Helpers:**
- `_generate_random_int(low, high)` — generates a random integer in `[low, high]` using `random.randint()`, swapping bounds if inverted.
- `_generate_random_float(low, high, precision, step)` — generates a random float in `[low, high]`, applies step snapping if `step > 0`, and rounds to the given precision.
- `_snap_to_step(value, low, step)` — snaps a float to the nearest step grid point anchored at `low`.

### Frontend Architecture (js/random_nodes.js)

A single JavaScript extension handles both node types:

1. **`beforeRegisterNodeDef`** hook: For each random node type, chain onto `onNodeCreated` to add two buttons:
   - **"New random value"**: Reads `range_from` and `range_to` widget values, generates a random number client-side, sets the `value` widget, and sets `randomized` to `false`.
   - **"Use current: 0"**: Sets the `value` widget to the last known generated value and sets `randomized` to `false`. The button label updates dynamically to show the current number.

2. **`nodeCreated`** hook: Attaches an `onExecuted` handler to each random node instance. When the backend returns `PreviewText` UI data, the handler:
   - Reads the generated value from `output.text` (the `PreviewText` output key) and parses it as a number.
   - Updates the `value` widget to reflect the generated number.
   - Updates the "Use current: {N}" button label.
   - Stores the value for the "Use current" button callback.

**Client-side randomization** (for buttons) is a convenience feature — it uses `Math.random()` for ints and does not apply step/precision logic for floats (it uses the widget's step constraint instead). The authoritative randomization with full constraint handling happens on the backend when `randomized` is `True`.

### Input Validation

Both nodes implement `validate_inputs()` for parameter sanity checks:
- For Random Float: `precision` must be >= 1.

Equal ranges (`range_from == range_to`) are permitted — the node returns the single possible value. This supports dynamic workflows where upstream-computed range values may converge.

## Rationale

- **`fingerprint_inputs` over `not_idempotent`**: The nodes are only non-reproducible when `randomized=True`. Using `fingerprint_inputs` preserves caching for the deterministic case, which is the common case when the user has locked in a value.
- **Backend randomization over frontend-only**: The Random Float node has `step` and `precision` constraints that require careful arithmetic (step snapping, rounding). Doing this authoritatively on the backend avoids duplicating the logic in JavaScript and guarantees consistency.
- **Frontend buttons as convenience**: The buttons provide immediate UI feedback without queueing a prompt. They use simplified client-side randomization because full constraint handling is not necessary for a "quick pick" — the user can always toggle `randomized=True` for a backend-generated value.
- **`PreviewText` for widget sync**: When the backend generates a value, it returns it via `ui.PreviewText(str(result))` so the frontend can update the `value` widget via the `onExecuted` handler. This uses a verified V3 UI helper pattern (rather than a plain dict) and adds a useful visual display of the generated value on the node.

## Considered Alternatives

| Decision | Chosen Shape | Alternatives Considered | Trade-Off Summary |
|----------|--------------|-------------------------|-------------------|
| Caching strategy | `fingerprint_inputs` conditional on `randomized` | `not_idempotent=True` (always skip cache) | `not_idempotent` wastes computation when `randomized=False` — the common steady-state. `fingerprint_inputs` preserves caching for the deterministic case. |
| Randomization location | Backend (Python `random` module) with frontend convenience buttons | Frontend-only (`widget.beforeQueued` + `Math.random()`) | Frontend-only cannot enforce step/precision constraints for floats and would duplicate range-swap logic. Backend is authoritative; frontend buttons are a UX shortcut. |
| Widget sync mechanism | `ui.PreviewText(str(result))` in `NodeOutput` + `onExecuted` handler | `PromptServer.send_sync()` custom event; plain dict `ui={"random_value": [result]}` | `PreviewText` is a verified V3 UI helper that also displays the value on the node. Plain dicts are unverified with V3 `NodeOutput(ui=...)`. Custom server events add unnecessary complexity. |
| Range validation | Allow equal range (returns the constant value) | `validate_inputs` rejects `range_from == range_to` | Equal ranges are mathematically valid (degenerate uniform distribution). Allowing them supports dynamic workflows where upstream-computed range values may converge. Rejecting would block the entire prompt for a benign edge case. |

## Pattern Alignment

- **V3 node class structure**: Follows `io.ComfyNode` subclass pattern with `define_schema()` + `execute()` classmethods — established in all `comfyui-custom-node-skills/skill_test_nodes/` files and `comfyui-json-nodes/nodes.py`.
- **Module-level helpers**: Private `_helper()` functions at the top of `nodes.py` — established in `comfyui-json-nodes/nodes.py`.
- **Output identifier casing**: `io.*.Output()` identifiers use SCREAMING_SNAKE_CASE (`VALUE`, `RANGE_FROM`, `RANGE_TO`, `PRECISION`, `STEP`), matching every existing output in `comfyui-json-nodes/nodes.py` (e.g. `VALUE`, `KEY`) and `comfyui-custom-node-skills/skill_test_nodes/nodes_outputs.py` (e.g. `SUM`, `PRODUCT`). Input identifiers (`range_from`, `range_to`, `precision`, `step`, `value`, `randomized`) remain lowercase, matching the same convention's `io.*.Input()` calls.
- **Extension registration**: `ComfyExtension` subclass + `comfy_entrypoint()` in `__init__.py` — established in `comfyui-json-nodes/__init__.py`.
- **`pyproject.toml` layout**: `[project]` + `[project.urls]` + `[tool.comfy]` — established in `comfyui-json-nodes/pyproject.toml`.
- **Test naming**: `verify_*.py` in `tests/` — established in `comfyui-json-nodes/tests/` and `constraints.md`.
- **Frontend extension**: `app.registerExtension()` with lifecycle hooks — established in `comfyui-custom-node-skills/skill_test_nodes/js/skill_test_extension.js`.
- **Departure: `WEB_DIRECTORY`**: The json-nodes project has no frontend code. This project adds `WEB_DIRECTORY = "./js"` and a `js/` directory, which is a standard V3 pattern documented in the `comfyui-node-packaging` skill but new to this author's node packages.

## Detailed Steps

### Step 1: Update constraints.md with Project Conventions and Behavioral Invariants

Update `docs/agents/project-manifest/constraints.md`:
- Record the chosen author prefix (`Mistralys_`) and node category (`random`) under "Project Conventions".
- Replace the provisional `<!-- TODO: verify -->` behavioral invariants (seed sentinel and `not_idempotent=True`) with the actual decisions:
  - **Randomization control**: `randomized` boolean socketless input — `True` generates a new value, `False` returns the stored `value` widget value. No seed input.
  - **Conditional caching**: `fingerprint_inputs()` returns `time.time()` when `randomized=True` (force re-execution) and a deterministic fingerprint when `randomized=False` (allow caching). `not_idempotent=True` is not used.
  - **Equal ranges permitted**: `range_from == range_to` is allowed and returns the single possible value.

### Step 2: Create nodes.py with Helper Functions and Node Classes

Create `nodes.py` at the project root with:

**Module-level helpers:**
- `_generate_random_int(low, high)` — swap bounds if `low > high`, return `random.randint(low, high)`.
- `_snap_to_step(value, low, step)` — snap `value` to the nearest step grid point anchored at `low`: `low + round((value - low) / step) * step`. Clamp the result to not exceed `high`.
- `_generate_random_float(low, high, precision, step)` — swap bounds if needed, generate `random.uniform(low, high)`, apply step snapping if `step > 0`, round to `precision` decimal places.

**RandomIntNode** (`Mistralys_RandomInt`):
- Schema inputs: `range_from` (Int, default 0), `range_to` (Int, default 1), `value` (Int, default 0, socketless), `randomized` (Boolean, default `False`, socketless).
- Schema outputs: `VALUE` (Int), `RANGE_FROM` (Int), `RANGE_TO` (Int).
- `fingerprint_inputs`: return `time.time()` if `randomized`, else `f"{value}"`.
- `execute`: if `randomized`, call `_generate_random_int(range_from, range_to)` and return result + `ui=ui.PreviewText(str(result))`; else return `value` directly.

**RandomFloatNode** (`Mistralys_RandomFloat`):
- Schema inputs: `range_from` (Float, default 0.0), `range_to` (Float, default 1.0), `precision` (Int, default 2, min 1), `step` (Float, default 0.0, min 0.0), `value` (Float, default 0.0, socketless), `randomized` (Boolean, default `False`, socketless).
- Schema outputs: `VALUE` (Float), `RANGE_FROM` (Float), `RANGE_TO` (Float), `PRECISION` (Int), `STEP` (Float).
- `fingerprint_inputs`: return `time.time()` if `randomized`, else `f"{value}"`.
- `validate_inputs`: reject if `precision < 1`.
- `execute`: if `randomized`, call `_generate_random_float(range_from, range_to, precision, step)` and return result + `ui=ui.PreviewText(str(result))`; else return `value` (rounded to `precision`) directly.

### Step 3: Create __init__.py with Extension Registration

Create `__init__.py` at the project root:
- Import `RandomIntNode` and `RandomFloatNode` from `.nodes`.
- Define `WEB_DIRECTORY = "./js"`.
- Define `RandomNodesExtension(ComfyExtension)` with `get_node_list()` returning both node classes.
- Define `async def comfy_entrypoint()` returning a `RandomNodesExtension` instance.

### Step 4: Create js/random_nodes.js Frontend Extension

Create `js/random_nodes.js`:

**Extension registration** (`app.registerExtension`):
- `name`: `"mistralys.random_nodes"`

**`beforeRegisterNodeDef` hook** — for node IDs `Mistralys_RandomInt` and `Mistralys_RandomFloat`:
- Chain onto `onNodeCreated`.
- Inside `onNodeCreated`, initialize `_lastGeneratedValue` from the `value` widget's current value: `this._lastGeneratedValue = this.widgets.find(w => w.name === "value").value;`. This ensures the "Use current: {N}" button reflects the actual persisted value after a saved workflow is reloaded, rather than a hardcoded `0`/`0.0`.
- Add a **"New random value"** button widget:
  - Read `range_from` and `range_to` widget values.
  - For int: generate `Math.floor(Math.random() * (high - low + 1)) + low`.
  - For float: generate `Math.random() * (high - low) + low`, round to the precision widget value's decimal places.
  - Set the `value` widget to the generated number.
  - Set the `randomized` widget to `false`.
- Add a **"Use current: {N}"** button widget, with the initial label reflecting `_lastGeneratedValue`:
  - Set the `value` widget to `_lastGeneratedValue`.
  - Set the `randomized` widget to `false`.
  - Label updates dynamically via `onExecuted`.

**`nodeCreated` hook** — for each random node instance:
- Attach `onExecuted` handler:
  - Read the generated value from `output.text` (the `PreviewText` output key) and parse it as a number (`parseInt` for int nodes, `parseFloat` for float nodes).
  - Update the `value` widget with the received value.
  - Update `_lastGeneratedValue`.
  - Find the "Use current" button and update its label to `"Use current: {value}"`.

### Step 5: Create pyproject.toml

Create `pyproject.toml` at the project root following the `comfyui-json-nodes` pattern:
- `name`: `"comfyui-random-nodes"`
- `version`: `"1.0.0"`
- `description`: `"ComfyUI V3 custom nodes to generate random integer and float values."`
- `license`: `"MIT"`
- `requires-python`: `">=3.10"`
- `authors`: `[{ name = "Mistralys" }]`
- `[tool.comfy] PublisherId = "Mistralys"`

### Step 6: Create changelog.md

Create `changelog.md` at the project root with a `## 1.0.0` section documenting the initial release with both nodes.

### Step 7: Create Unit Tests

**`tests/verify_random_int.py`:**
- Mock `comfy_api.latest` module (`io`, `ui` classes).
- Test `_generate_random_int`: correct range, bound swapping, single-value range.
- Test `RandomIntNode.execute`: randomized=True produces value in range, randomized=False returns stored value.
- Test `RandomIntNode.fingerprint_inputs`: returns float (time) when randomized, deterministic string when not.
- Test `RandomIntNode.execute` with equal range: returns the single possible value.
- Test passthrough outputs: `range_from` and `range_to` match inputs.
- Test `RandomIntNode.define_schema()`: returns `node_id="Mistralys_RandomInt"` and `category="random"`.

**`tests/verify_random_float.py`:**
- Mock `comfy_api.latest` module.
- Test `_generate_random_float`: correct range, bound swapping, precision rounding.
- Test `_snap_to_step`: correct step snapping, edge cases (step=0 passthrough, step larger than range).
- Test `RandomFloatNode.execute`: randomized=True produces value in range with correct precision, randomized=False returns stored value.
- Test step constraint: generated values align to step grid.
- Test `RandomFloatNode.validate_inputs`: rejects `precision < 1`, accepts valid parameters.
- Test `RandomFloatNode.execute` with equal range: returns the single possible value.
- Test passthrough outputs: all range/precision/step values match inputs.
- Test `RandomFloatNode.define_schema()`: returns `node_id="Mistralys_RandomFloat"` and `category="random"`.

### Step 8: Update Documentation

**`docs/agents/project-manifest/tech-stack.md`** — resolve the `<!-- TODO: verify — update node count when implementation begins -->` marker under Architecture by documenting the actual node count (2: `RandomIntNode`, `RandomFloatNode`).

**`docs/agents/project-manifest/constraints.md`** — add author prefix (`Mistralys_`) and category (`random`) under Project Conventions. Replace provisional seed-handling and `not_idempotent` behavioral invariants with actual decisions (`randomized` boolean toggle, conditional `fingerprint_inputs` caching, equal ranges permitted).

**`docs/agents/project-manifest/api-surface.md`** — populate with:
- Extension table (RandomNodesExtension, comfy_entrypoint)
- Helper functions table (_generate_random_int, _generate_random_float, _snap_to_step)
- Node class summary table
- Detailed per-node I/O tables for RandomIntNode and RandomFloatNode

**`docs/agents/project-manifest/data-flows.md`** — replace the general template with node-specific flows:
- Extension loading flow (unchanged)
- RandomIntNode execution flow (randomized vs. stored value paths)
- RandomFloatNode execution flow (includes step snapping and precision rounding)
- Frontend widget synchronization flow

**`docs/agents/project-manifest/file-tree.md`** — update to reflect actual files: remove `<!-- planned -->` markers, add `js/` directory.

**`README.md`** — expand with: project description, node descriptions (inputs, outputs, buttons), installation instructions, requirements (ComfyUI with V3 API support).

## Dependencies

- Steps 1 must complete before Step 2 (prefix/category documented before use).
- Steps 2 and 4 are independent (backend and frontend can be built in parallel).
- Step 3 depends on Step 2 (imports node classes).
- Step 5 has no dependencies.
- Step 6 has no dependencies.
- Step 7 depends on Step 2 (tests import node classes and helpers).
- Step 8 depends on Steps 2–5 (documents the implemented code).

## Required Components

- `nodes.py` — new file: node classes and helpers
- `__init__.py` — new file: extension registration
- `js/random_nodes.js` — new file: frontend extension
- `pyproject.toml` — new file: package metadata
- `changelog.md` — new file: project changelog
- `tests/verify_random_int.py` — new file: RandomIntNode unit tests
- `tests/verify_random_float.py` — new file: RandomFloatNode unit tests
- `docs/agents/project-manifest/constraints.md` — existing file: update
- `docs/agents/project-manifest/api-surface.md` — existing file: update
- `docs/agents/project-manifest/data-flows.md` — existing file: update
- `docs/agents/project-manifest/file-tree.md` — existing file: update
- `docs/agents/project-manifest/tech-stack.md` — existing file: update
- `README.md` — existing file: update

## Assumptions

- `ui.PreviewText` output is accessible in the frontend's `onExecuted` handler via the `output.text` key, allowing the handler to read and parse the generated value.
- The `addWidget("button", ...)` LiteGraph API is available in the ComfyUI frontend for adding interactive buttons to nodes.
- Widget values updated via JavaScript (`widget.value = x`) are serialized into the workflow JSON and persist across saves/loads.
- The `randomized` socketless boolean widget renders as a toggle/checkbox in the ComfyUI UI.

## Constraints

- **V3 API only** — no V1 fallback or `NODE_CLASS_MAPPINGS`.
- **No external dependencies** — only `random`, `time` from stdlib and `comfy_api.latest` from ComfyUI.
- **Author prefix `Mistralys_`** — all node IDs must use this prefix.
- **Category `random`** — all nodes use this flat category.
- **Two-tier testing** — unit tests in `tests/verify_*.py` + manual testing in live ComfyUI.

## Out of Scope

- Seed-based reproducibility (the spec uses a `randomized` boolean toggle, not a seed input).
- Additional random distribution types (normal, exponential, etc.).
- Batch generation (generating multiple random values in one execution).
- Custom connection types (both nodes use built-in `Int` and `Float` types).
- Localization / i18n support.

## Acceptance Criteria

- AC-01: `RandomIntNode` generates a random integer within `[range_from, range_to]` when `randomized=True`, and returns the `value` widget value when `randomized=False`.
- AC-02: `RandomFloatNode` generates a random float within `[range_from, range_to]`, rounded to `precision` decimal places, snapped to `step` grid (if `step > 0`), when `randomized=True`, and returns the `value` widget value when `randomized=False`.
- AC-03: Both nodes pass through all input range parameters as outputs.
- AC-04: Both nodes use `fingerprint_inputs` to allow caching when `randomized=False` and force re-execution when `randomized=True`.
- AC-05: Both nodes allow `range_from == range_to` (returns the single possible value). `RandomFloatNode` validates `precision >= 1` via `validate_inputs`.
- AC-06: The frontend extension adds "New random value" and "Use current: {N}" buttons to both node types.
- AC-07: The "New random value" button generates a client-side random value within the widget range, sets the `value` widget, and sets `randomized` to `false`.
- AC-08: The `onExecuted` handler updates the `value` widget and the "Use current" button label with the backend-generated value.
- AC-09: All node IDs use the `Mistralys_` prefix and `random` category.
- AC-10: The extension registers via `ComfyExtension` + `comfy_entrypoint()` with `WEB_DIRECTORY = "./js"`.
- AC-11: Unit tests cover randomized/stored execution paths, range validation, helper functions, and passthrough outputs.
- AC-12: `pyproject.toml` is valid and follows the `comfyui-json-nodes` pattern.
- AC-13: Documentation (api-surface.md, data-flows.md, file-tree.md, constraints.md, README.md, changelog.md) is updated to reflect the implementation.

## Testing Strategy

**Unit tests (mock-based):** Two `verify_*.py` scripts mock ComfyUI internals (`comfy_api.latest`) and test node logic in isolation. Each script covers: helper function behavior, execute method output for both `randomized=True` and `randomized=False` paths, `fingerprint_inputs` behavior, `validate_inputs` rejection/acceptance, and passthrough output correctness.

**Manual integration tests:** After deployment to a ComfyUI instance, manually verify: nodes appear in the "random" category menu, widget rendering (range inputs, socketless value/randomized, buttons), button behavior (client-side randomization, value locking), output connections to downstream nodes, caching behavior (re-execution when randomized, caching when stored), and workflow save/load persistence of widget values.

## Test Plan

- `tests/verify_random_int.py` — `RandomIntNode.define_schema()` returns `node_id="Mistralys_RandomInt"` and `category="random"` — AC-09
- `tests/verify_random_int.py` — `_generate_random_int` respects bounds and swaps inverted ranges — AC-01
- `tests/verify_random_int.py` — `RandomIntNode.execute` with `randomized=True` returns value in range — AC-01
- `tests/verify_random_int.py` — `RandomIntNode.execute` with `randomized=False` returns `value` input — AC-01
- `tests/verify_random_int.py` — `RandomIntNode.execute` passthrough outputs match inputs — AC-03
- `tests/verify_random_int.py` — `RandomIntNode.fingerprint_inputs` returns time when randomized, deterministic string when not — AC-04
- `tests/verify_random_int.py` — `RandomIntNode.execute` with equal range returns the single possible value — AC-05
- `tests/verify_random_float.py` — `_generate_random_float` respects bounds, precision, and step — AC-02
- `tests/verify_random_float.py` — `_snap_to_step` snaps correctly, handles edge cases — AC-02
- `tests/verify_random_float.py` — `RandomFloatNode.execute` with `randomized=True` returns value with correct precision and step alignment — AC-02
- `tests/verify_random_float.py` — `RandomFloatNode.execute` with `randomized=False` returns `value` input — AC-02
- `tests/verify_random_float.py` — `RandomFloatNode.execute` passthrough outputs match inputs — AC-03
- `tests/verify_random_float.py` — `RandomFloatNode.fingerprint_inputs` conditional behavior — AC-04
- `tests/verify_random_float.py` — `RandomFloatNode.validate_inputs` rejects precision < 1, accepts valid params — AC-05
- `tests/verify_random_float.py` — `RandomFloatNode.execute` with equal range returns the single possible value — AC-05
- `tests/verify_random_float.py` — `RandomFloatNode.define_schema()` returns `node_id="Mistralys_RandomFloat"` and `category="random"` — AC-09

## Documentation Updates

- `docs/agents/project-manifest/tech-stack.md` — resolve the `<!-- TODO: verify -->` marker under Architecture by documenting the actual node count (2: `RandomIntNode`, `RandomFloatNode`)
- `docs/agents/project-manifest/constraints.md` — add author prefix `Mistralys_` and category `random` under Project Conventions; replace provisional behavioral invariants with actual decisions
- `docs/agents/project-manifest/api-surface.md` — populate extension, helpers, and node class schemas
- `docs/agents/project-manifest/data-flows.md` — replace template with node-specific execution flows
- `docs/agents/project-manifest/file-tree.md` — update to reflect actual files, add `js/` directory
- `README.md` — expand with project description, node documentation, installation instructions
- `changelog.md` — new file documenting initial 1.0.0 release

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| **`PreviewText` output key format may differ from expected `output.text`** | Verify the exact key structure of `PreviewText` output in the `onExecuted` handler during live ComfyUI integration testing. Check `skill_test_nodes/nodes_outputs.py` PreviewText example for reference. |
| **`addWidget("button")` API may behave differently across ComfyUI frontend versions** | Use the exact pattern from `comfyui-node-frontend` skill documentation. Test in a live ComfyUI instance early. |
| **Widget value updates via JS may not persist in workflow save/load** | Verify serialization behavior in live ComfyUI. If needed, use `widget.serializeValue` hook to ensure persistence. |
| **Step snapping arithmetic may introduce floating-point drift** | Use `round()` with the specified `precision` as the final step after all arithmetic. Add targeted unit tests for edge cases (very small steps, very large ranges). |
| **Client-side button randomization may differ from backend randomization** | Document that buttons are convenience features using simplified randomization. The `randomized=True` toggle path is the authoritative backend-generated value. |

## Recommended Workflow
- **Workflow:** ledger
- **Rationale:** The plan spans backend nodes, a frontend JavaScript extension, unit tests, packaging, and multi-file documentation updates — distinct concerns that benefit from structured QA, review, and documentation stages.
