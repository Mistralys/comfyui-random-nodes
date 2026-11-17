# Random Int

Generates a random integer within a range, or reuses the last stored value.

## Inputs
- **range_from**: Minimum integer value to generate.
- **range_to**: Maximum integer value to generate. If it is lower than `range_from`, the bounds are swapped.
- **value**: The randomized value. Reused when `randomized` is off.
- **randomized**: When on, every run generates a new value. When off, the stored `value` is returned.

## Outputs
- **VALUE**: The generated (or stored) integer value.
- **RANGE_FROM**: Passthrough of `range_from`.
- **RANGE_TO**: Passthrough of `range_to`.

## Notes
The **New random value** button rolls a value and stores it in `value` without queuing a run, and turns `randomized` off. **Use current** turns `randomized` off to keep the value shown.
