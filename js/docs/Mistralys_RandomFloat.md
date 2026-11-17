# Random Float

Generates a random float within a range, with precision and step control, or reuses the last stored value.

## Inputs
- **range_from**: Minimum float value to generate.
- **range_to**: Maximum float value to generate. If it is lower than `range_from`, the bounds are swapped.
- **precision**: Number of decimal places (at least 1).
- **step**: Snap generated values to this step grid, anchored at `range_from`. `0.0` means no stepping.
- **value**: The randomized value. Reused when `randomized` is off.
- **randomized**: When on, every run generates a new value. When off, the stored `value` is returned.

## Outputs
- **VALUE**: The generated (or stored) float value.
- **RANGE_FROM**, **RANGE_TO**, **PRECISION**, **STEP**: Passthroughs of the matching inputs.

## Notes
The **New random value** button rolls a value and stores it in `value` without queuing a run, and turns `randomized` off.
