# Plan

## Plan Audit Cycles
- Audits: none — Plan Auditor v1.7.0
- Architectural Reviews: none — Plan Architect Reviewer v2.2.0

## Prior Project Context
One prior project (2026-08-12-random-nodes) implemented RandomIntNode and RandomFloatNode with the shared `setupRandomNode` frontend pattern and conditional `fingerprint_inputs` caching. This plan reuses both patterns directly.

## Summary
Add a `RandomFloatFromPresetNode` that lets the user define a list of preferred float values as a comma-separated string (e.g. `"3.2, 4.2, 4.8, 5.2"`) and either select a specific value from a frontend dropdown, have one picked at random, or cycle through them sequentially on each execution. The `presets` input has a socket, so a single STRING source node can feed the same presets list to multiple preset nodes for centralized management. The node uses a `mode` combo (`fixed` / `random` / `cycle`) instead of the existing boolean `randomized` toggle, with conditional `fingerprint_inputs` caching.

## Architectural Context
- **`nodes.py`** contains all node classes and module-level helpers. `RandomFloatNode` is the closest analog — it has `value` (socketless FLOAT), `randomized` (socketless BOOLEAN), conditional `fingerprint_inputs`, and `execute` returning `io.NodeOutput` with optional `ui.PreviewText`.
- **`__init__.py`** registers all nodes in `RandomNodesExtension.get_node_list()`.
- **`js/random_nodes.js`** enhances nodes with client-side buttons and `onExecuted` widget sync. The `setupRandomNode(node, generateFn)` pattern adds "New random value" and "Use current: {N}" buttons.

## Approach / Architecture

### Backend (`nodes.py`)
Add a `_parse_presets(presets_str)` helper that parses a comma-separated string into a sorted list of unique floats, and a `_pick_random_preset(presets_str)` helper that returns a random choice from the parsed list. Add `RandomFloatFromPresetNode` with four inputs:
- `presets` (STRING, multiline) — comma-separated float values, default `"3.2, 4.2, 4.8, 5.2"`
- `value` (FLOAT, socketless) — the stored/selected value, default `1.0`, step `0.1`
- `mode` (COMBO, socketless) — selection mode: `fixed` (use stored value), `random` (pick randomly), `cycle` (step through sequentially); default `"fixed"`
- `cycle_index` (INT, socketless) — current position in the cycle, default `0`; user-adjustable to set starting position

Three outputs: `VALUE` (FLOAT), `PRESETS` (STRING, passthrough), and `INDEX` (INT, the 0-based index of the selected preset; in fixed mode, passes through `cycle_index`).

`validate_inputs` rejects empty preset lists (after parsing). `fingerprint_inputs` returns a deterministic fingerprint for `fixed` mode and `time.time()` for `random` and `cycle` modes. `execute` dispatches on `mode`:
- `fixed`: returns stored `value`, passes through `cycle_index` as INDEX
- `random`: returns `random.choice()` from parsed presets with `PreviewText`
- `cycle`: picks `presets[cycle_index % len(presets)]`, computes `next_index`, returns value with `PreviewText` encoding both value and next_index

### Frontend (`js/random_nodes.js`)
Add a `setupPresetNode(node)` function that:
1. Reads the `presets` widget string and parses it into a float array.
2. Adds a **combo widget** (`node.addWidget("combo", ...)`) populated with the parsed values, plus a callback that sets `value` and sets `mode` to `"fixed"`.
3. Adds "New random value" (picks random from presets) and "Use current: {N}" buttons using the existing pattern.
4. Watches the `presets` widget for changes and rebuilds the combo options.

Wire `onExecuted` to sync the `value` widget from `PreviewText` output. In cycle mode, also parse and sync the `cycle_index` widget from the pipe-delimited PreviewText format (`"value|next_index"`), and update the "Use current" button label to show position: `"Use current: {value} ({position}/{total})"`.

## Rationale
- **Generic name "Random Float from Preset"** rather than CFG-specific: the node has no CFG-specific logic. It selects a random float from a user-defined list, equally useful for denoise strength, guidance scale, clip skip, or any discrete-valued parameter.
- **Presets as a STRING input with socket** rather than extension settings: keeps presets per-node and per-workflow by default, while the socket enables centralized sharing — connect a single Primitive STRING node to multiple preset nodes to share one presets list across a workflow. No external state or server-side storage needed.
- **Single node** rather than two (editor + selector): the presets list is small enough to edit inline, and socket-based sharing covers the centralization use case without a dedicated editor node.
- **Not extending RandomFloat**: RandomFloat generates from a continuous range with step snapping. Preset selection is a discrete paradigm — a `random.choice()` from a list, not a `random.uniform()` from a range. Merging these would muddle the node's single responsibility.
- **Frontend combo widget** added dynamically: `io.Combo.Input` requires static options at schema definition time. Since presets are user-editable, the combo must be created client-side from the parsed presets string.
- **Cycle mode** alongside fixed and random: enables systematic A/B comparison — step through each preset value in order rather than relying on random selection to cover them all. The `cycle_index` as a socketless input lets the user transparently inspect and adjust the current position.
- **`mode` combo instead of `randomized` boolean**: cycle cannot be expressed as a boolean. A three-way combo (`fixed` / `random` / `cycle`) cleanly replaces the boolean and is self-documenting.

## Considered Alternatives

| Decision | Chosen Shape | Alternatives Considered | Trade-Off Summary |
|----------|--------------|-------------------------|-------------------|
| Node naming | "Random Float from Preset" (generic) | "Random CFG" (parameter-specific) | Generic name enables use for any float parameter, not just CFG. No logic changes needed. |
| Presets storage | STRING input with socket | Extension settings (global per-user), UserData API (server file), Two-node editor+selector | STRING input with socket gives per-node editing by default plus centralized sharing via upstream connection. Extension settings would be global-only and require frontend-to-backend plumbing. |
| Selection UI | Dynamic frontend combo widget | Static `io.Combo.Input`, No dropdown (buttons only) | Static combo can't reflect user-edited presets. Buttons-only gives poor UX for lists > 3 items. Dynamic combo rebuilds on presets change and gives clean dropdown selection. |
| Randomization model | `random.choice()` from parsed list | `random.uniform()` with step (like RandomFloat) | Discrete selection from a curated list is the entire point; continuous range generation is already served by RandomFloat. |
| Mode control | Combo: fixed / random / cycle | Boolean `randomized` toggle (no cycle) | Cycle mode adds systematic testing capability; a boolean can't express three states. |
| Cycle index storage | Socketless INT input (user-visible, adjustable) | Hidden internal state, Server-side counter | Socketless input follows project conventions, is transparent, and lets the user reset or adjust the starting position. |
| Weighted presets | **Deferred** — flat equal-probability selection | Syntax like `"3.2:1, 4.2:3, 5.0:5"` with `random.choices()` | Adds parsing complexity for an edge case. Can be added later without breaking existing preset strings (unweighted entries default to weight 1). |
| Integer preset variant | **Future topic** — separate "Random Int from Preset" node | Dual INT/FLOAT output on this node, type toggle input | Separate node keeps single responsibility clear. Same architecture, just INT parsing and output. |

## Pattern Alignment
- `fingerprint_inputs` conditional caching — follows `nodes.py` L108–L111 pattern (adapted: `fixed` → deterministic, `random`/`cycle` → `time.time()`).
- `socketless` value + mode inputs — follows `nodes.py` L96–L99 socketless convention.
- `setupRandomNode`-style frontend enhancement — follows `js/random_nodes.js` L35–L57 pattern (adapted for combo widget + preset parsing + cycle index sync).
- `onExecuted` widget sync via `PreviewText` — follows `js/random_nodes.js` L80–L98 pattern.
- Module-level private helpers `_parse_presets()` / `_pick_random_preset()` — follows `_generate_random_int` / `_generate_random_float` pattern.
- `Mistralys_` node ID prefix, `random` category — follows `constraints.md`.

## Detailed Steps

### Step 1: Add `_parse_presets()` and `_pick_random_preset()` helpers to `nodes.py`

Add two module-level helper functions:

```python
def _parse_presets(presets_str):
    values = []
    for part in presets_str.split(","):
        part = part.strip()
        if part:
            try:
                values.append(float(part))
            except ValueError:
                continue
    return sorted(set(values))


def _pick_random_preset(presets_str):
    values = _parse_presets(presets_str)
    if not values:
        return 1.0
    return random.choice(values)
```

Place these after the existing `_generate_random_float()` function.

### Step 2: Add `RandomFloatFromPresetNode` class to `nodes.py`

Add the node class after `RandomFloatNode`:

```python
class RandomFloatFromPresetNode(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="Mistralys_RandomFloatFromPreset",
            display_name="Random Float from Preset",
            category="random",
            inputs=[
                io.String.Input("presets",
                    default="3.2, 4.2, 4.8, 5.2",
                    multiline=True,
                    tooltip="Comma-separated list of float values to choose from.",
                ),
                io.Float.Input("value", default=1.0, min=0.0, max=100.0, step=0.1, socketless=True,
                    tooltip="The selected or randomized value. Reused when mode is 'fixed'.",
                ),
                io.Combo.Input("mode", options=["fixed", "random", "cycle"], default="fixed", socketless=True,
                    tooltip="fixed: use stored value. random: pick randomly. cycle: step through presets sequentially.",
                ),
                io.Int.Input("cycle_index", default=0, min=0, socketless=True,
                    tooltip="Current position in the preset cycle. Advances automatically in cycle mode; adjustable manually.",
                ),
            ],
            outputs=[
                io.Float.Output("VALUE",
                    tooltip="The selected (or randomly picked) float value.",
                ),
                io.String.Output("PRESETS",
                    tooltip="Passthrough of the presets input value.",
                ),
                io.Int.Output("INDEX",
                    tooltip="The index of the selected preset (0-based). In fixed mode, passes through cycle_index.",
                ),
            ],
        )

    @classmethod
    def validate_inputs(cls, presets):
        if not _parse_presets(presets):
            return "presets must contain at least one valid number"
        return True

    @classmethod
    def fingerprint_inputs(cls, presets, value, mode, cycle_index):
        if mode == "fixed":
            return f"{value}"
        return time.time()

    @classmethod
    def execute(cls, presets, value, mode, cycle_index):
        if mode == "random":
            result = _pick_random_preset(presets)
            return io.NodeOutput(result, presets, 0, ui=ui.PreviewText(str(result)))
        if mode == "cycle":
            values = _parse_presets(presets)
            idx = cycle_index % len(values)
            result = values[idx]
            next_index = (cycle_index + 1) % len(values)
            return io.NodeOutput(result, presets, idx, ui=ui.PreviewText(f"{result}|{next_index}"))
        return io.NodeOutput(value, presets, cycle_index)
```

### Step 3: Register `RandomFloatFromPresetNode` in `__init__.py`

Add `RandomFloatFromPresetNode` to the import list and `get_node_list()` return value:

```python
from .nodes import (
    RandomIntNode,
    RandomFloatNode,
    RandomFloatFromPresetNode,
)
```

```python
async def get_node_list(self) -> list[type[io.ComfyNode]]:
    return [
        RandomIntNode,
        RandomFloatNode,
        RandomFloatFromPresetNode,
    ]
```

### Step 4: Add frontend support in `js/random_nodes.js`

Add a `RANDOM_FLOAT_FROM_PRESET_NODE` constant and the following functions:

**`parsePresets(str)`** — splits the presets string on commas, parses each to float, filters NaN, returns sorted unique array.

**`setupPresetNode(node)`**:
1. Gets `presets`, `value`, `mode`, and `cycle_index` widgets.
2. Parses presets into a float array.
3. Sets `value` widget to the first parsed preset (initializes the node with a meaningful default from the list).
4. Adds a combo widget listing each preset value as a string option. When the user selects a value, sets `value` widget to that float and `mode` to `"fixed"`.
5. Adds "New random value" button — picks a random element from the parsed presets, sets `value`, sets `mode` to `"fixed"`.
6. Adds "Use current: {N}" button — same pattern as existing nodes.
7. Hooks the `presets` widget's callback to rebuild the combo options and set `value` to the first preset when the text changes.

**Socket-connected behavior:** When `presets` is connected via socket, ComfyUI hides the presets widget. The combo dropdown and "New random value" button read from the widget value, which won't reflect the upstream value until execution. After execution, `onExecuted` syncs the `value` widget from the backend output, so the "Use current" button works correctly regardless.

**`beforeRegisterNodeDef`** — add an `else if` branch for `RANDOM_FLOAT_FROM_PRESET_NODE` that chains `setupPresetNode` onto `onNodeCreated`.

**`nodeCreated`** — add `RANDOM_FLOAT_FROM_PRESET_NODE` to the guard condition. Wire `onExecuted` to:
1. Parse `PreviewText` output text.
2. If text contains `|` (cycle mode): split into `[value, next_index]`, update `value` widget, update `cycle_index` widget, compute position `((next_index - 1 + total) % total) + 1` (1-indexed) and update the button label to `"Use current: {value} ({position}/{total})"`.
3. If text has no `|` (random mode): update `value` widget, update button label to `"Use current: {value}"`.
4. Update `_lastGeneratedValue`.

### Step 5: Add `tests/verify_random_float_from_preset.py`

Create mock-based unit tests covering:
1. **Preset parsing** — valid comma-separated string parsed correctly; whitespace trimmed; duplicates removed; invalid entries skipped; empty string returns empty list.
2. **Random selection** — `execute` with `mode="random"` returns a value that is a member of the parsed presets.
3. **Cycle selection** — `execute` with `mode="cycle"` returns `presets[cycle_index % len(presets)]` and includes the next index in `PreviewText`.
4. **Cycle wrapping** — `execute` with `cycle_index >= len(presets)` wraps correctly.
5. **Stored value passthrough** — `execute` with `mode="fixed"` returns the `value` input unchanged and passes through `cycle_index` as INDEX.
6. **Validation** — `validate_inputs` rejects empty/all-invalid presets strings; accepts valid presets.
7. **Fingerprint** — `fingerprint_inputs` returns deterministic string when `mode="fixed"`; returns `time.time()` for `"random"` and `"cycle"`.
8. **PreviewText output** — `execute` with `mode="random"` returns `PreviewText` with value only; `mode="cycle"` returns `PreviewText` with `"value|next_index"` format.

### Step 6: Update documentation

Update the following files per the AGENTS.md documentation maintenance rules:

- **`docs/agents/project-manifest/api-surface.md`** — add `RandomFloatFromPresetNode` to the Summary table and a Node Detail section documenting inputs/outputs/methods.
- **`docs/agents/project-manifest/data-flows.md`** — add a "RandomFloatFromPresetNode Execution Flow" section covering all three modes, and update the "Frontend Widget Synchronization Flow" section to cover preset node dropdown and cycle index sync behavior.
- **`docs/agents/project-manifest/file-tree.md`** — add `tests/verify_random_float_from_preset.py` entry.
- **`README.md`** — add Random Float from Preset node to the node listing with usage description covering all three modes.
- **`changelog.md`** — add entry for the new node.
- **`AGENTS.md`** — update Project File Layout to include the new test file.

## Dependencies
- Steps 1–2 (backend) and Step 4 (frontend) are independent and can be developed in parallel.
- Step 3 (registration) depends on Step 2.
- Step 5 (tests) depends on Steps 1–2.
- Step 6 (documentation) depends on all other steps.

## Required Components
- `nodes.py` — modified (new helper functions + new node class)
- `__init__.py` — modified (new import + registration)
- `js/random_nodes.js` — modified (new preset node frontend support)
- `tests/verify_random_float_from_preset.py` — new file
- `docs/agents/project-manifest/api-surface.md` — modified
- `docs/agents/project-manifest/data-flows.md` — modified
- `docs/agents/project-manifest/file-tree.md` — modified
- `README.md` — modified
- `changelog.md` — modified
- `AGENTS.md` — modified

## Assumptions
- The default presets `"3.2, 4.2, 4.8, 5.2"` are a reasonable starting example for the most common use case (CFG scale values), while the generic node name communicates that any float values can be used.
- The schema default for `value` is `1.0` (safe fallback); the frontend overrides this to the first parsed preset on node creation.
- A `max` of `100.0` on the `value` widget is sufficient for typical use cases.
- The combo widget added by the frontend is a non-serialized UI convenience; the authoritative state is the `presets` string and `value` float.
- Users will typically define 3–15 preset values; the combo dropdown UX works well at this scale.
- When `presets` is connected via socket, users will primarily use `random` or `cycle` mode; the combo dropdown and "New random value" button are secondary UI for inline-editing mode.
- Cycle mode advancement relies on frontend widget sync via `PreviewText`. When multiple prompts are batch-queued simultaneously, all queued runs share the same `cycle_index` snapshot from queue time, so they may select the same preset. This is acceptable; users can use ComfyUI's "Auto Queue" mode for sequential single-run cycling.

## Constraints
- No external dependencies — stdlib only (satisfied: uses `random.choice`, `float()`, `str.split`).
- V3 API only — no V1 compatibility.
- `Mistralys_` node ID prefix, `random` category.
- Conditional `fingerprint_inputs` caching — not `not_idempotent`.

## Out of Scope
- Global preset management via ComfyUI extension settings or UserData API (socket-based sharing covers this use case).
- Preset import/export functionality.
- Validation that preset values are within a "typical" range for any specific parameter (the node accepts any float).
- Extending RandomFloatNode with preset capabilities (different paradigm).
- Weighted preset probability (deferred — can be added later with backward-compatible `"value:weight"` syntax).
- Integer preset variant (future topic — separate "Random Int from Preset" node with same architecture).

## Acceptance Criteria

- AC-01: `RandomFloatFromPresetNode` is registered with node ID `Mistralys_RandomFloatFromPreset`, display name "Random Float from Preset", category `random`.
- AC-02: The node accepts a multiline `presets` STRING input with socket (default `"3.2, 4.2, 4.8, 5.2"`), a socketless `value` FLOAT input (default `1.0`, step `0.1`), a socketless `mode` COMBO input (options: `fixed` / `random` / `cycle`, default `"fixed"`), and a socketless `cycle_index` INT input (default `0`).
- AC-03: When `mode="random"`, `execute` returns a `random.choice()` from the parsed presets list and includes `ui.PreviewText` with the value.
- AC-04: When `mode="fixed"`, `execute` returns the stored `value` unchanged, with `cycle_index` passed through as INDEX output.
- AC-04a: All execution paths pass through `presets` as the second output.
- AC-05: When `mode="cycle"`, `execute` returns `presets[cycle_index % len(presets)]`, outputs the current index as INDEX, and includes `ui.PreviewText` with `"value|next_index"` format.
- AC-05a: Cycle mode wraps correctly when `cycle_index >= len(presets)`.
- AC-06: `validate_inputs` rejects presets strings that contain no valid float values.
- AC-07: `fingerprint_inputs` returns a deterministic string when `mode="fixed"` and `time.time()` for `"random"` and `"cycle"`.
- AC-08: The frontend adds a dropdown (combo widget) populated from the parsed `presets` string. Selecting a value sets `value` and sets `mode` to `"fixed"`.
- AC-09: The frontend adds "New random value" and "Use current: {N}" buttons following the existing pattern.
- AC-10: The frontend `onExecuted` handler syncs the `value` widget (and `cycle_index` in cycle mode) from the `PreviewText` backend output.
- AC-11: In cycle mode, the "Use current" button label shows position: `"Use current: {value} ({position}/{total})"`.
- AC-12: The frontend rebuilds the dropdown options when the `presets` text widget changes and sets `value` to the first preset.
- AC-13: `tests/verify_random_float_from_preset.py` covers preset parsing, random selection, cycle selection with wrapping, stored value passthrough, validation, fingerprinting, and PreviewText output formats.
- AC-14: Documentation is updated: `api-surface.md`, `data-flows.md`, `file-tree.md`, `README.md`, `changelog.md`.

## Testing Strategy
Mock-based unit tests (`verify_random_float_from_preset.py`) validate all backend logic without a live ComfyUI instance. Frontend behavior (dropdown, button interactions, widget sync, cycle index display) is validated manually in a live ComfyUI instance.

## Test Plan
- `tests/verify_random_float_from_preset.py` — `_parse_presets` returns sorted unique floats from comma-separated input — AC-02
- `tests/verify_random_float_from_preset.py` — `_parse_presets` handles whitespace, duplicates, invalid entries, empty string — AC-06
- `tests/verify_random_float_from_preset.py` — `execute` with `mode="random"` returns a member of the parsed presets — AC-03
- `tests/verify_random_float_from_preset.py` — `execute` with `mode="random"` returns `PreviewText` UI output with value only — AC-03
- `tests/verify_random_float_from_preset.py` — `execute` with `mode="fixed"` returns the `value` input unchanged and passes through `cycle_index` — AC-04
- `tests/verify_random_float_from_preset.py` — `execute` with `mode="cycle"` returns `presets[cycle_index % len]` and includes `"value|next_index"` in PreviewText — AC-05
- `tests/verify_random_float_from_preset.py` — `execute` with `mode="cycle"` wraps `cycle_index` correctly — AC-05a
- `tests/verify_random_float_from_preset.py` — `validate_inputs` returns error string for empty/invalid presets — AC-06
- `tests/verify_random_float_from_preset.py` — `validate_inputs` returns `True` for valid presets — AC-06
- `tests/verify_random_float_from_preset.py` — `fingerprint_inputs` returns deterministic string when `mode="fixed"` — AC-07
- `tests/verify_random_float_from_preset.py` — `fingerprint_inputs` returns float (time) when `mode="random"` or `mode="cycle"` — AC-07

## Documentation Updates
- `docs/agents/project-manifest/api-surface.md` — add `RandomFloatFromPresetNode` summary row and detail section with inputs/outputs/methods
- `docs/agents/project-manifest/data-flows.md` — add RandomFloatFromPresetNode execution flow section covering all three modes; update frontend sync section
- `docs/agents/project-manifest/file-tree.md` — add `tests/verify_random_float_from_preset.py` entry
- `README.md` — add Random Float from Preset node description with all three modes
- `changelog.md` — add new node entry
- `AGENTS.md` — update file layout section to include new test file

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| **Dynamic combo widget may not serialize correctly** | The combo is a non-serialized UI convenience only. The authoritative state is the `presets` string + `value` float, which are standard serialized widgets. The combo is rebuilt from `presets` on node creation. |
| **Presets text with only invalid entries** | `validate_inputs` rejects execution if no valid floats are parsed. `_pick_random_preset` also falls back to `1.0` as defense-in-depth. |
| **Frontend combo rebuild on presets change may cause flickering** | The combo widget is rebuilt cleanly by replacing the options array. LiteGraph handles this without visual artifacts for small option lists. |
| **Cycle index not advancing in batch-queued runs** | Documented as a known limitation. Each queued prompt carries a snapshot of widget values from queue time. Cycle advances correctly in single-run and "Auto Queue" modes. |
| **`io.Combo.Input` may not support `socketless`** | Verify during implementation against V3 API skills. If unsupported, use `io.String.Input` with frontend combo rendering, or accept the default socket behavior. |

## Recommended Workflow
- **Workflow:** standalone
- **Rationale:** Single-module feature addition within well-understood patterns; one new node class, one frontend enhancement, and one test file — a single developer session suffices.
