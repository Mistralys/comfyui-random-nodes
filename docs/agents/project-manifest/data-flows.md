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

## RandomFloatFromPresetNode Execution Flow

1. `validate_inputs(presets)` runs during the validation phase, rejecting `presets` strings that parse (via `_parse_presets()`) to no valid floats.
2. Before execution, `fingerprint_inputs(presets, value, mode, cycle_index)` returns a deterministic string derived from `value` when `mode="fixed"`, and `time.time()` for `mode="random"` or `mode="cycle"`.
3. `execute()` dispatches on `mode`:
   - `"random"`: calls `_pick_random_preset(presets)`, returns the result as `VALUE`, passes through `presets` as `PRESETS`, `0` as `INDEX`, plus `ui=ui.PreviewText(str(result))`.
   - `"cycle"`: parses `presets` via `_parse_presets()`, indexes at `cycle_index % len(values)`, computes `next_index = (cycle_index + 1) % len(values)`, returns the value as `VALUE`, the current index as `INDEX`, plus `ui=ui.PreviewText(f"{result}|{next_index}")` encoding both the value and the next cycle position.
   - `"fixed"`: returns the stored `value` as `VALUE`, passes through `presets` as `PRESETS` and `cycle_index` unchanged as `INDEX`.

## Frontend Widget Synchronization Flow

1. `beforeRegisterNodeDef` chains onto `onNodeCreated` for both node types, adding "New random value" and "Use current: {N}" button widgets, and initializing `_lastGeneratedValue` from the current `value` widget.
2. "New random value" generates a client-side random number (via `Math.random()`, ignoring backend step/precision constraints for floats beyond widget precision), sets the `value` widget, and sets `randomized` to `false`.
3. "Use current: {N}" sets the `value` widget to `_lastGeneratedValue` and sets `randomized` to `false`.
4. `nodeCreated` attaches an `onExecuted` handler that reads the backend-generated value from `output.text` (the `PreviewText` UI output), parses it, updates the `value` widget, updates `_lastGeneratedValue`, and refreshes the "Use current" button label.

### RandomFloatFromPresetNode Frontend Flow

1. `beforeRegisterNodeDef` chains `setupPresetNode` onto `onNodeCreated`, which parses the `presets` widget string via `parsePresets()`, initializes `value` to the first parsed preset, and adds a dynamic **combo widget** populated with the parsed values, plus "New random value" and "Use current: {N}" buttons.
2. Selecting a combo option sets `value` to the chosen float and sets `mode` to `"fixed"`. "New random value" picks a random preset client-side and does the same. Both bypass the backend's `random`/`cycle` modes for immediate UI feedback.
3. The `presets` widget's callback is wrapped to rebuild the combo's options and reset `value` to the first preset whenever the presets text changes.
4. `nodeCreated` attaches an `onExecuted` handler that parses `output.text`: if it contains `"|"` (cycle mode), it splits into `[value, next_index]`, updates the `value` and `cycle_index` widgets, and sets the "Use current" button label to `"Use current: {value} ({position}/{total})"`; otherwise (random mode) it updates only `value` and the button label to `"Use current: {value}"`.

> **Idempotency note:** All three nodes rely on `fingerprint_inputs`, not `not_idempotent`, since caching should be preserved when randomization is inactive (`randomized=False` or `mode="fixed"`).
