import random
import time
from comfy_api.latest import io, ui


def _generate_random_int(low, high):
    """Generate a random integer in [low, high], swapping bounds if inverted."""
    if low > high:
        low, high = high, low
    return random.randint(low, high)


def _snap_to_step(value, low, high, step):
    """Snap value to the nearest step grid point anchored at low, clamped to high."""
    if step <= 0:
        return value
    snapped = low + round((value - low) / step) * step
    return min(snapped, high)


def _generate_random_float(low, high, precision, step):
    """Generate a random float in [low, high], apply step snapping, and round to precision."""
    if low > high:
        low, high = high, low
    value = random.uniform(low, high)
    value = _snap_to_step(value, low, high, step)
    return round(value, precision)


def _parse_presets(presets_str):
    """Parse a comma-separated string into a sorted list of unique floats, skipping invalid entries."""
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
    """Pick a random value from the parsed presets, falling back to 1.0 if none are valid."""
    values = _parse_presets(presets_str)
    if not values:
        return 1.0
    return random.choice(values)


class RandomIntNode(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="Mistralys_RandomInt",
            display_name="Random Int",
            category="random",
            inputs=[
                io.Int.Input("range_from", default=0,
                    tooltip="Minimum integer value to generate.",
                ),
                io.Int.Input("range_to", default=1,
                    tooltip="Maximum integer value to generate.",
                ),
                io.Int.Input("value", default=0, socketless=True,
                    tooltip="The randomized value. Reused when 'randomized' is off.",
                ),
                io.Boolean.Input("randomized", default=False, socketless=True,
                    tooltip="Whether to generate a new random value on the next run.",
                ),
            ],
            outputs=[
                io.Int.Output("VALUE",
                    tooltip="The generated (or stored) integer value.",
                ),
                io.Int.Output("RANGE_FROM",
                    tooltip="Passthrough of the input value.",
                ),
                io.Int.Output("RANGE_TO",
                    tooltip="Passthrough of the input value.",
                ),
            ],
        )

    @classmethod
    def fingerprint_inputs(cls, range_from, range_to, value, randomized):
        if randomized:
            return time.time()
        return f"{value}"

    @classmethod
    def execute(cls, range_from, range_to, value, randomized):
        if randomized:
            result = _generate_random_int(range_from, range_to)
            return io.NodeOutput(result, range_from, range_to, ui=ui.PreviewText(str(result)))
        return io.NodeOutput(value, range_from, range_to)


class RandomFloatNode(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="Mistralys_RandomFloat",
            display_name="Random Float",
            category="random",
            inputs=[
                io.Float.Input("range_from", default=0.0,
                    tooltip="Minimum float value to generate.",
                ),
                io.Float.Input("range_to", default=1.0,
                    tooltip="Maximum float value to generate.",
                ),
                io.Int.Input("precision", default=2, min=1,
                    tooltip="Number of decimal places.",
                ),
                io.Float.Input("step", default=0.0, min=0.0,
                    tooltip="Snap generated values to this step grid. 0.0 means no stepping.",
                ),
                io.Float.Input("value", default=0.0, socketless=True,
                    tooltip="The randomized value. Reused when 'randomized' is off.",
                ),
                io.Boolean.Input("randomized", default=False, socketless=True,
                    tooltip="Whether to generate a new random value on the next run.",
                ),
            ],
            outputs=[
                io.Float.Output("VALUE",
                    tooltip="The generated (or stored) float value.",
                ),
                io.Float.Output("RANGE_FROM",
                    tooltip="Passthrough of the input value.",
                ),
                io.Float.Output("RANGE_TO",
                    tooltip="Passthrough of the input value.",
                ),
                io.Int.Output("PRECISION",
                    tooltip="Passthrough of the input value.",
                ),
                io.Float.Output("STEP",
                    tooltip="Passthrough of the input value.",
                ),
            ],
        )

    @classmethod
    def validate_inputs(cls, precision):
        if precision < 1:
            return "precision must be at least 1"
        return True

    @classmethod
    def fingerprint_inputs(cls, range_from, range_to, precision, step, value, randomized):
        if randomized:
            return time.time()
        return f"{value}"

    @classmethod
    def execute(cls, range_from, range_to, precision, step, value, randomized):
        if randomized:
            result = _generate_random_float(range_from, range_to, precision, step)
            return io.NodeOutput(result, range_from, range_to, precision, step, ui=ui.PreviewText(str(result)))
        return io.NodeOutput(round(value, precision), range_from, range_to, precision, step)


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
