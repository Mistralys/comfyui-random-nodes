# Key Data Flows

---

## Extension Loading

1. ComfyUI calls `comfy_entrypoint()` in `__init__.py`
2. Returns a `RandomNodesExtension` instance
3. ComfyUI calls `get_node_list()` → receives all node classes
4. Each node's `define_schema()` is called to register inputs/outputs/metadata
5. `WEB_DIRECTORY = "./js"` causes ComfyUI to load `js/random_nodes.js` on the frontend

## RandomIntNode Execution Flow

1. Before execution, ComfyUI calls `fingerprint_inputs(range_from, range_to, value, randomized)`.
   - If `randomized=True`: returns `time.time()`, forcing re-execution every run.
   - If `randomized=False`: returns a deterministic string derived from `value`, allowing ComfyUI to reuse a cached result.
2. `execute()` runs:
   - If `randomized=True`: calls `_generate_random_int(range_from, range_to)`, returns the result as `VALUE` plus `ui=ui.PreviewText(str(result))` for frontend widget sync.
   - If `randomized=False`: returns the stored `value` directly.
3. `range_from` and `range_to` are always passed through as `RANGE_FROM`/`RANGE_TO` outputs.

## RandomFloatNode Execution Flow

1. `validate_inputs(precision)` runs during the validation phase, rejecting `precision < 1`.
2. Before execution, `fingerprint_inputs(range_from, range_to, precision, step, value, randomized)` follows the same conditional pattern as `RandomIntNode`.
3. `execute()` runs:
   - If `randomized=True`: calls `_generate_random_float(range_from, range_to, precision, step)`, which generates a value via `random.uniform()`, applies `_snap_to_step()` if `step > 0`, and rounds to `precision` decimal places. Returns the result as `VALUE` plus `ui=ui.PreviewText(str(result))`.
   - If `randomized=False`: returns `value` rounded to `precision`.
4. `range_from`, `range_to`, `precision`, and `step` are always passed through as outputs.

## Frontend Widget Synchronization Flow

1. `beforeRegisterNodeDef` chains onto `onNodeCreated` for both node types, adding "New random value" and "Use current: {N}" button widgets, and initializing `_lastGeneratedValue` from the current `value` widget.
2. "New random value" generates a client-side random number (via `Math.random()`, ignoring backend step/precision constraints for floats beyond widget precision), sets the `value` widget, and sets `randomized` to `false`.
3. "Use current: {N}" sets the `value` widget to `_lastGeneratedValue` and sets `randomized` to `false`.
4. `nodeCreated` attaches an `onExecuted` handler that reads the backend-generated value from `output.text` (the `PreviewText` UI output), parses it, updates the `value` widget, updates `_lastGeneratedValue`, and refreshes the "Use current" button label.

> **Idempotency note:** Both nodes rely on `fingerprint_inputs`, not `not_idempotent`, since caching should be preserved when `randomized=False`.
