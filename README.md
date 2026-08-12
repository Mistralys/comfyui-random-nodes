# comfyui-random-nodes

Selection of ComfyUI V3 custom nodes to generate random numbers, with interactive "New random value" / "Use current" buttons for locking in a generated value.

## Requirements

- ComfyUI with V3 API support (`comfy_api.latest`)
- Python 3.10+
- No external (pip) dependencies

## Installation

Clone or copy this repository into your ComfyUI `custom_nodes/` directory, then restart ComfyUI.

## Nodes

Both nodes appear under the **random** category.

### Random Int

Generates a random integer value within a range.

**Inputs**

| Name | Type | Notes |
|---|---|---|
| `range_from` | Int | Minimum value (default `0`). Negative values allowed. |
| `range_to` | Int | Maximum value (default `1`). Negative values allowed. |
| `value` (widget only) | Int | The randomized value (default `0`). |
| `randomized` (widget only) | Boolean | When `True`, generates a new random value on the next run. |

**Buttons**

- **New random value** — sets `value` to a random int within range and sets `randomized` to `false`.
- **Use current: {N}** — sets `value` to the last generated int and sets `randomized` to `false`.

**Outputs**

| Name | Type | Notes |
|---|---|---|
| `VALUE` | Int | The generated (or stored) value. |
| `RANGE_FROM` | Int | Passthrough of `range_from`. |
| `RANGE_TO` | Int | Passthrough of `range_to`. |

### Random Float

Generates a random float value within a range, with precision and step control.

**Inputs**

| Name | Type | Notes |
|---|---|---|
| `range_from` | Float | Minimum value (default `0.0`). Negative values allowed. |
| `range_to` | Float | Maximum value (default `1.0`). Negative values allowed. |
| `precision` | Int | Number of decimal places (default `2`, minimum `1`). |
| `step` | Float | Snaps generated values to this step grid (default `0.0` = no stepping). |
| `value` (widget only) | Float | The randomized value (default `0.0`). |
| `randomized` (widget only) | Boolean | When `True`, generates a new random value on the next run. |

**Buttons**

- **New random value** — sets `value` to a random float within range and sets `randomized` to `false`.
- **Use current: {N}** — sets `value` to the last generated float and sets `randomized` to `false`.

**Outputs**

| Name | Type | Notes |
|---|---|---|
| `VALUE` | Float | The generated (or stored) value. |
| `RANGE_FROM` | Float | Passthrough of `range_from`. |
| `RANGE_TO` | Float | Passthrough of `range_to`. |
| `PRECISION` | Int | Passthrough of `precision`. |
| `STEP` | Float | Passthrough of `step`. |

## Behavior Notes

- Both nodes generate a new value only when `randomized` is `True`; otherwise they return the stored `value`.
- Caching is controlled via `fingerprint_inputs`: it forces re-execution when `randomized=True` and allows caching (based on `value`) when `randomized=False`.
- `range_from == range_to` is a valid input and returns the single possible value.
