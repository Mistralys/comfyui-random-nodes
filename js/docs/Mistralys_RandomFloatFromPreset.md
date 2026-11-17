# Random Float from Preset

Picks a float from a comma-separated list of preset values.

## Inputs
- **presets**: Comma-separated list of float values. Invalid entries are skipped; the remaining values are sorted and de-duplicated. At least one valid number is required.
- **value**: The selected or randomized value. Reused when `mode` is `fixed`.
- **mode**:
  - `fixed`: Use the stored `value`.
  - `random`: Pick a random preset on each run.
  - `cycle`: Step through the presets in order, wrapping around at the end.
- **cycle_index**: Current position in the preset cycle. Advances automatically in `cycle` mode and can be adjusted manually.

## Outputs
- **VALUE**: The selected (or randomly picked) float value.
- **PRESETS**: Passthrough of `presets`.
- **INDEX**: The 0-based index of the selected preset. In `fixed` mode, passes through `cycle_index`.
