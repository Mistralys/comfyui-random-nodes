# Public API Surface

---

## Extension

| Symbol | Type | Purpose |
|--------|------|---------|
| `RandomNodesExtension` | `ComfyExtension` subclass | Registers all node classes with ComfyUI |
| `comfy_entrypoint()` | Module-level function | Entry point called by ComfyUI on load; returns a `RandomNodesExtension` instance |

## Private Helper Functions

| Function | Purpose |
|---|---|
| `_generate_random_int(low, high)` | Generates a random integer in `[low, high]` using `random.randint()`, swapping bounds if inverted. |
| `_snap_to_step(value, low, high, step)` | Snaps `value` to the nearest step grid point anchored at `low`, clamped to not exceed `high`. Returns `value` unchanged if `step <= 0`. |
| `_generate_random_float(low, high, precision, step)` | Generates a random float in `[low, high]` via `random.uniform()`, applies step snapping (if `step > 0`), and rounds to `precision` decimal places. Swaps bounds if inverted. |
| `_parse_presets(presets_str)` | Parses a comma-separated string into a sorted list of unique floats, skipping invalid entries. |
| `_pick_random_preset(presets_str)` | Picks a random value from the parsed presets via `_parse_presets()`; falls back to `1.0` if none are valid. |

## Module-Level Constants

None.

## Node Classes

### Summary

| Class | Node ID | Display Name | Category | Schema Flags |
|-------|---------|-------------|----------|--------------|
| `RandomIntNode` | `Mistralys_RandomInt` | Random Int | `random` | — |
| `RandomFloatNode` | `Mistralys_RandomFloat` | Random Float | `random` | `validate_inputs` |
| `RandomFloatFromPresetNode` | `Mistralys_RandomFloatFromPreset` | Random Float from Preset | `random` | `validate_inputs` |

### Node Detail

#### `RandomIntNode` — `Mistralys_RandomInt` / "Random Int"

| I/O | Name | Type | Notes |
|-----|------|------|-------|
| Input | `range_from` | `Int` | Default `0`. Minimum value of the generated range. |
| Input | `range_to` | `Int` | Default `1`. Maximum value of the generated range. |
| Input | `value` (socketless) | `Int` | Default `0`. Stored value returned when `randomized=False`. |
| Input | `randomized` (socketless) | `Boolean` | Default `False`. `True` generates a new random value on execute. |
| Output | `VALUE` | `Int` | The generated (or stored) integer. |
| Output | `RANGE_FROM` | `Int` | Passthrough of `range_from`. |
| Output | `RANGE_TO` | `Int` | Passthrough of `range_to`. |

`fingerprint_inputs`: returns `time.time()` when `randomized=True` (forces re-execution); returns a deterministic string derived from `value` when `randomized=False` (allows caching).

#### `RandomFloatNode` — `Mistralys_RandomFloat` / "Random Float"

| I/O | Name | Type | Notes |
|-----|------|------|-------|
| Input | `range_from` | `Float` | Default `0.0`. Minimum value of the generated range. |
| Input | `range_to` | `Float` | Default `1.0`. Maximum value of the generated range. |
| Input | `precision` | `Int` | Default `2`, min `1`. Number of decimal places. |
| Input | `step` | `Float` | Default `0.0`, min `0.0`. Snap grid size; `0.0` disables stepping. |
| Input | `value` (socketless) | `Float` | Default `0.0`. Stored value returned when `randomized=False`. |
| Input | `randomized` (socketless) | `Boolean` | Default `False`. `True` generates a new random value on execute. |
| Output | `VALUE` | `Float` | The generated (or stored) float. |
| Output | `RANGE_FROM` | `Float` | Passthrough of `range_from`. |
| Output | `RANGE_TO` | `Float` | Passthrough of `range_to`. |
| Output | `PRECISION` | `Int` | Passthrough of `precision`. |
| Output | `STEP` | `Float` | Passthrough of `step`. |

`validate_inputs`: rejects `precision < 1`.

`fingerprint_inputs`: returns `time.time()` when `randomized=True` (forces re-execution); returns a deterministic string derived from `value` when `randomized=False` (allows caching).

#### `RandomFloatFromPresetNode` — `Mistralys_RandomFloatFromPreset` / "Random Float from Preset"

| I/O | Name | Type | Notes |
|-----|------|------|-------|
| Input | `presets` | `String` (multiline) | Default `"3.2, 4.2, 4.8, 5.2"`. Comma-separated float values; has a socket for upstream sharing. |
| Input | `value` (socketless) | `Float` | Default `1.0`, step `0.1`. Stored value returned when `mode="fixed"`. |
| Input | `mode` (socketless) | `Combo` | Options `fixed` / `random` / `cycle`. Default `"fixed"`. |
| Input | `cycle_index` (socketless) | `Int` | Default `0`. Current position in the preset cycle. |
| Output | `VALUE` | `Float` | The selected (or randomly/cyclically picked) value. |
| Output | `PRESETS` | `String` | Passthrough of `presets`. |
| Output | `INDEX` | `Int` | 0-based index of the selected preset; passes through `cycle_index` in `fixed` mode. |

`validate_inputs`: rejects `presets` strings that contain no valid float values (via `_parse_presets()`).

`fingerprint_inputs`: returns a deterministic string derived from `value` when `mode="fixed"`; returns `time.time()` for `mode="random"` and `mode="cycle"`.

`execute`: dispatches on `mode` — `random` calls `_pick_random_preset()`; `cycle` indexes into `_parse_presets()` at `cycle_index % len(values)` and computes the next index; `fixed` returns the stored `value` and passes through `cycle_index` as `INDEX`.
